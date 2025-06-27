# app/services/payment_processor.py - Payment Processing Integration
import os
from typing import Dict, Optional
from flask import current_app
import json
import hashlib
import hmac

# Try to import stripe - graceful fallback if not available
try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False
    print("Warning: Stripe not installed. Payment processing will use simulation mode.")

class PaymentProcessor:
    """Payment processor with support for multiple payment providers"""
    
    def __init__(self, provider: str = 'stripe'):
        self.provider = provider
        self.simulation_mode = os.getenv('PAYMENT_SIMULATION_MODE', 'false').lower() == 'true'
        
        if provider == 'stripe' and STRIPE_AVAILABLE and not self.simulation_mode:
            self.stripe_secret_key = os.getenv('STRIPE_SECRET_KEY')
            self.stripe_publishable_key = os.getenv('STRIPE_PUBLISHABLE_KEY')
            self.stripe_webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
            
            if not self.stripe_secret_key:
                print("Warning: Stripe secret key not found. Using simulation mode.")
                self.simulation_mode = True
            else:
                stripe.api_key = self.stripe_secret_key
        else:
            self.simulation_mode = True
    
    def create_subscription(self, user_id: int, plan, payment_details: Dict) -> Dict:
        """Create a new subscription"""
        
        if self.simulation_mode:
            return self._simulate_subscription_creation(user_id, plan, payment_details)
        
        if self.provider == 'stripe':
            return self._stripe_create_subscription(user_id, plan, payment_details)
        
        return {'success': False, 'error': 'Unsupported payment provider'}
    
    def process_upgrade_payment(self, subscription, new_plan, proration: Dict, payment_details: Dict) -> Dict:
        """Process payment for subscription upgrade"""
        
        if self.simulation_mode:
            return self._simulate_upgrade_payment(subscription, new_plan, proration)
        
        if self.provider == 'stripe':
            return self._stripe_process_upgrade(subscription, new_plan, proration, payment_details)
        
        return {'success': False, 'error': 'Unsupported payment provider'}
    
    def cancel_subscription(self, subscription, immediate: bool = False) -> Dict:
        """Cancel subscription"""
        
        if self.simulation_mode:
            return self._simulate_subscription_cancellation(subscription, immediate)
        
        if self.provider == 'stripe':
            return self._stripe_cancel_subscription(subscription, immediate)
        
        return {'success': False, 'error': 'Unsupported payment provider'}
    
    def process_token_purchase(self, user_id: int, token_amount: int, price_cents: int, payment_details: Dict) -> Dict:
        """Process one-time token purchase"""
        
        if self.simulation_mode:
            return self._simulate_token_purchase(user_id, token_amount, price_cents)
        
        if self.provider == 'stripe':
            return self._stripe_process_token_purchase(user_id, token_amount, price_cents, payment_details)
        
        return {'success': False, 'error': 'Unsupported payment provider'}
    
    def verify_webhook(self, payload: bytes, signature: str) -> Dict:
        """Verify webhook signature and return event data"""
        
        if self.simulation_mode:
            return self._simulate_webhook_event()
        
        if self.provider == 'stripe':
            return self._stripe_verify_webhook(payload, signature)
        
        return {'success': False, 'error': 'Unsupported payment provider'}
    
    # Stripe Implementation
    def _stripe_create_subscription(self, user_id: int, plan, payment_details: Dict) -> Dict:
        """Create Stripe subscription"""
        try:
            from app.models import User
            user = User.query.get(user_id)
            
            # Create or get customer
            customer = self._stripe_get_or_create_customer(user, payment_details)
            
            # Create subscription
            subscription = stripe.Subscription.create(
                customer=customer.id,
                items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': plan.display_name,
                            'description': f'{plan.monthly_token_limit} tokens per month'
                        },
                        'unit_amount': plan.monthly_price_cents,
                        'recurring': {'interval': 'month'}
                    }
                }],
                payment_behavior='default_incomplete',
                expand=['latest_invoice.payment_intent'],
                metadata={
                    'user_id': user_id,
                    'plan_name': plan.name
                }
            )
            
            return {
                'success': True,
                'subscription_id': subscription.id,
                'customer_id': customer.id,
                'client_secret': subscription.latest_invoice.payment_intent.client_secret,
                'status': subscription.status
            }
            
        except Exception as e:
            current_app.logger.error(f"Stripe subscription creation failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _stripe_get_or_create_customer(self, user, payment_details: Dict):
        """Get existing Stripe customer or create new one"""
        
        # Try to find existing customer
        customers = stripe.Customer.list(email=user.email, limit=1)
        if customers.data:
            return customers.data[0]
        
        # Create new customer
        customer_data = {
            'email': user.email,
            'name': user.username,
            'metadata': {'user_id': user.id}
        }
        
        # Add payment method if provided
        if 'payment_method_id' in payment_details:
            customer_data['payment_method'] = payment_details['payment_method_id']
            customer_data['invoice_settings'] = {
                'default_payment_method': payment_details['payment_method_id']
            }
        
        return stripe.Customer.create(**customer_data)
    
    def _stripe_process_upgrade(self, subscription, new_plan, proration: Dict, payment_details: Dict) -> Dict:
        """Process Stripe subscription upgrade"""
        try:
            # Get Stripe subscription
            stripe_sub = stripe.Subscription.retrieve(subscription.stripe_subscription_id)
            
            # Update subscription with new plan
            updated_sub = stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                items=[{
                    'id': stripe_sub['items']['data'][0]['id'],
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': new_plan.display_name,
                            'description': f'{new_plan.monthly_token_limit} tokens per month'
                        },
                        'unit_amount': new_plan.monthly_price_cents,
                        'recurring': {'interval': 'month'}
                    }
                }],
                proration_behavior='create_prorations'
            )
            
            return {
                'success': True,
                'subscription_id': updated_sub.id,
                'proration_amount': proration['amount_due']
            }
            
        except Exception as e:
            current_app.logger.error(f"Stripe upgrade failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _stripe_cancel_subscription(self, subscription, immediate: bool) -> Dict:
        """Cancel Stripe subscription"""
        try:
            if immediate:
                cancelled_sub = stripe.Subscription.delete(subscription.stripe_subscription_id)
            else:
                cancelled_sub = stripe.Subscription.modify(
                    subscription.stripe_subscription_id,
                    cancel_at_period_end=True
                )
            
            return {
                'success': True,
                'subscription_id': cancelled_sub.id,
                'status': cancelled_sub.status,
                'cancel_at_period_end': cancelled_sub.cancel_at_period_end
            }
            
        except Exception as e:
            current_app.logger.error(f"Stripe cancellation failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _stripe_process_token_purchase(self, user_id: int, token_amount: int, price_cents: int, payment_details: Dict) -> Dict:
        """Process one-time token purchase with Stripe"""
        try:
            from app.models import User
            user = User.query.get(user_id)
            
            # Create payment intent
            payment_intent = stripe.PaymentIntent.create(
                amount=price_cents,
                currency='usd',
                payment_method=payment_details.get('payment_method_id'),
                confirmation_method='manual',
                confirm=True,
                description=f'{token_amount} tokens for {user.email}',
                metadata={
                    'user_id': user_id,
                    'token_amount': token_amount,
                    'type': 'token_purchase'
                }
            )
            
            return {
                'success': True,
                'payment_id': payment_intent.id,
                'status': payment_intent.status,
                'client_secret': payment_intent.client_secret if payment_intent.status == 'requires_action' else None
            }
            
        except Exception as e:
            current_app.logger.error(f"Stripe token purchase failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _stripe_verify_webhook(self, payload: bytes, signature: str) -> Dict:
        """Verify Stripe webhook"""
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, self.stripe_webhook_secret
            )
            return event
        except ValueError as e:
            current_app.logger.error(f"Invalid payload: {str(e)}")
            raise e
        except stripe.error.SignatureVerificationError as e:
            current_app.logger.error(f"Invalid signature: {str(e)}")
            raise e
    
    # Simulation Methods (for development/testing)
    def _simulate_subscription_creation(self, user_id: int, plan, payment_details: Dict) -> Dict:
        """Simulate subscription creation"""
        return {
            'success': True,
            'subscription_id': f'sim_sub_{user_id}_{plan.name}',
            'customer_id': f'sim_cust_{user_id}',
            'client_secret': 'sim_secret_12345',
            'status': 'active'
        }
    
    def _simulate_upgrade_payment(self, subscription, new_plan, proration: Dict) -> Dict:
        """Simulate upgrade payment"""
        return {
            'success': True,
            'subscription_id': subscription.stripe_subscription_id,
            'proration_amount': proration['amount_due']
        }
    
    def _simulate_subscription_cancellation(self, subscription, immediate: bool) -> Dict:
        """Simulate subscription cancellation"""
        return {
            'success': True,
            'subscription_id': subscription.stripe_subscription_id,
            'status': 'canceled' if immediate else 'active',
            'cancel_at_period_end': not immediate
        }
    
    def _simulate_token_purchase(self, user_id: int, token_amount: int, price_cents: int) -> Dict:
        """Simulate token purchase"""
        return {
            'success': True,
            'payment_id': f'sim_pi_{user_id}_{token_amount}',
            'status': 'succeeded',
            'client_secret': None
        }
    
    def _simulate_webhook_event(self) -> Dict:
        """Simulate webhook event"""
        return {
            'type': 'invoice.payment_succeeded',
            'data': {
                'object': {
                    'id': 'sim_invoice_123',
                    'customer': 'sim_cust_123',
                    'subscription': 'sim_sub_123'
                }
            }
        }
    
    # Utility Methods
    def get_public_key(self) -> Optional[str]:
        """Get publishable key for frontend"""
        if self.simulation_mode:
            return 'pk_test_simulation_mode'
        
        if self.provider == 'stripe':
            return self.stripe_publishable_key
        
        return None
    
    def create_setup_intent(self, customer_id: str) -> Dict:
        """Create setup intent for saving payment method"""
        if self.simulation_mode:
            return {
                'success': True,
                'client_secret': 'seti_sim_123_secret',
                'setup_intent_id': 'seti_sim_123'
            }
        
        if self.provider == 'stripe':
            try:
                setup_intent = stripe.SetupIntent.create(
                    customer=customer_id,
                    usage='off_session'
                )
                return {
                    'success': True,
                    'client_secret': setup_intent.client_secret,
                    'setup_intent_id': setup_intent.id
                }
            except Exception as e:
                return {'success': False, 'error': str(e)}
        
        return {'success': False, 'error': 'Unsupported provider'}
    
    def get_payment_methods(self, customer_id: str) -> Dict:
        """Get saved payment methods for customer"""
        if self.simulation_mode:
            return {
                'success': True,
                'payment_methods': [
                    {
                        'id': 'pm_sim_123',
                        'type': 'card',
                        'card': {
                            'brand': 'visa',
                            'last4': '4242',
                            'exp_month': 12,
                            'exp_year': 2025
                        }
                    }
                ]
            }
        
        if self.provider == 'stripe':
            try:
                payment_methods = stripe.PaymentMethod.list(
                    customer=customer_id,
                    type='card'
                )
                return {
                    'success': True,
                    'payment_methods': payment_methods.data
                }
            except Exception as e:
                return {'success': False, 'error': str(e)}
        
        return {'success': False, 'error': 'Unsupported provider'}
    
    def create_billing_portal_session(self, customer_id: str, return_url: str) -> Dict:
        """Create billing portal session for customer self-service"""
        if self.simulation_mode:
            return {
                'success': True,
                'url': f'{return_url}?simulation=billing_portal'
            }
        
        if self.provider == 'stripe':
            try:
                session = stripe.billing_portal.Session.create(
                    customer=customer_id,
                    return_url=return_url
                )
                return {
                    'success': True,
                    'url': session.url
                }
            except Exception as e:
                return {'success': False, 'error': str(e)}
        
        return {'success': False, 'error': 'Unsupported provider'}