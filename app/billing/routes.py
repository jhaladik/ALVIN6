# app/billing/routes.py - Billing and Subscription Management
from flask import request, jsonify, session, current_app
from app.billing import billing_bp
from app.models import User, BillingPlan, UserSubscription, TokenPurchase, TokenUsageLog
from app.utils.auth import login_required
from app.services.token_manager import token_manager
from app.services.payment_processor import PaymentProcessor
from app import db
from datetime import datetime, timedelta
import json

@billing_bp.route('/plans', methods=['GET'])
def get_billing_plans():
    """Get available billing plans"""
    plans = BillingPlan.query.filter_by(is_active=True, is_public=True).all()
    return jsonify({
        'success': True,
        'plans': [plan.to_dict() for plan in plans]
    })

@billing_bp.route('/subscription', methods=['GET'])
@login_required
def get_user_subscription():
    """Get current user's subscription details"""
    user_id = session['user_id']
    subscription = UserSubscription.query.filter_by(user_id=user_id).first()
    
    if not subscription:
        return jsonify({
            'success': True,
            'subscription': None,
            'needs_subscription': True
        })
    
    # Get usage analytics
    usage_analytics = token_manager.get_usage_analytics(user_id, 30)
    
    return jsonify({
        'success': True,
        'subscription': subscription.to_dict(),
        'usage_analytics': usage_analytics,
        'billing_history': get_billing_history_for_user(user_id)
    })

@billing_bp.route('/subscribe', methods=['POST'])
@login_required
def create_subscription():
    """Create new subscription"""
    data = request.get_json()
    user_id = session['user_id']
    plan_name = data.get('plan_name')
    payment_method = data.get('payment_method', 'stripe')
    
    # Get the plan
    plan = BillingPlan.query.filter_by(name=plan_name, is_active=True).first()
    if not plan:
        return jsonify({'error': 'Invalid plan'}), 400
    
    # Check if user already has subscription
    existing_subscription = UserSubscription.query.filter_by(user_id=user_id).first()
    if existing_subscription and existing_subscription.status == 'active':
        return jsonify({'error': 'User already has active subscription'}), 400
    
    try:
        # Process payment
        payment_processor = PaymentProcessor(payment_method)
        payment_result = payment_processor.create_subscription(
            user_id=user_id,
            plan=plan,
            payment_details=data.get('payment_details', {})
        )
        
        if not payment_result['success']:
            return jsonify({
                'error': 'Payment processing failed',
                'details': payment_result.get('error')
            }), 400
        
        # Create subscription
        now = datetime.utcnow()
        subscription = UserSubscription(
            user_id=user_id,
            plan_id=plan.id,
            status='active',
            current_period_start=now,
            current_period_end=now + timedelta(days=30),  # Monthly billing
            tokens_used_this_period=0,
            stripe_subscription_id=payment_result.get('subscription_id'),
            stripe_customer_id=payment_result.get('customer_id')
        )
        
        db.session.add(subscription)
        
        # Update user's plan and token limits
        user = User.query.get(user_id)
        user.plan = plan.name
        user.tokens_limit = plan.monthly_token_limit
        user.tokens_used = 0  # Reset for new billing period
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'subscription': subscription.to_dict(),
            'message': f'Successfully subscribed to {plan.display_name}'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Subscription creation failed: {str(e)}")
        return jsonify({'error': 'Subscription creation failed'}), 500

@billing_bp.route('/upgrade', methods=['POST'])
@login_required
def upgrade_subscription():
    """Upgrade existing subscription"""
    data = request.get_json()
    user_id = session['user_id']
    new_plan_name = data.get('plan_name')
    
    subscription = UserSubscription.query.filter_by(user_id=user_id).first()
    if not subscription:
        return jsonify({'error': 'No existing subscription found'}), 404
    
    new_plan = BillingPlan.query.filter_by(name=new_plan_name, is_active=True).first()
    if not new_plan:
        return jsonify({'error': 'Invalid plan'}), 400
    
    current_plan = subscription.plan
    
    try:
        # Calculate prorated charges
        days_remaining = (subscription.current_period_end - datetime.utcnow()).days
        proration = calculate_proration(current_plan, new_plan, days_remaining)
        
        # Process payment for upgrade
        payment_processor = PaymentProcessor()
        if proration['amount_due'] > 0:
            payment_result = payment_processor.process_upgrade_payment(
                subscription=subscription,
                new_plan=new_plan,
                proration=proration,
                payment_details=data.get('payment_details', {})
            )
            
            if not payment_result['success']:
                return jsonify({
                    'error': 'Payment processing failed',
                    'details': payment_result.get('error')
                }), 400
        
        # Update subscription
        subscription.plan_id = new_plan.id
        
        # Update user
        user = User.query.get(user_id)
        user.plan = new_plan.name
        user.tokens_limit = new_plan.monthly_token_limit
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'subscription': subscription.to_dict(),
            'proration': proration,
            'message': f'Successfully upgraded to {new_plan.display_name}'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Subscription upgrade failed: {str(e)}")
        return jsonify({'error': 'Upgrade failed'}), 500

@billing_bp.route('/cancel', methods=['POST'])
@login_required
def cancel_subscription():
    """Cancel subscription"""
    user_id = session['user_id']
    data = request.get_json()
    immediate = data.get('immediate', False)
    
    subscription = UserSubscription.query.filter_by(user_id=user_id).first()
    if not subscription:
        return jsonify({'error': 'No subscription found'}), 404
    
    try:
        # Cancel with payment processor
        payment_processor = PaymentProcessor()
        cancellation_result = payment_processor.cancel_subscription(
            subscription, immediate=immediate
        )
        
        if immediate:
            subscription.status = 'cancelled'
            subscription.current_period_end = datetime.utcnow()
            
            # Downgrade user to free plan
            user = User.query.get(user_id)
            free_plan = BillingPlan.query.filter_by(name='free').first()
            if free_plan:
                user.plan = 'free'
                user.tokens_limit = free_plan.monthly_token_limit
        else:
            subscription.status = 'cancelling'  # Will cancel at period end
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'subscription': subscription.to_dict(),
            'message': 'Subscription cancelled successfully',
            'effective_date': subscription.current_period_end.isoformat()
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Subscription cancellation failed: {str(e)}")
        return jsonify({'error': 'Cancellation failed'}), 500

@billing_bp.route('/buy-tokens', methods=['POST'])
@login_required
def buy_tokens():
    """Purchase additional tokens"""
    data = request.get_json()
    user_id = session['user_id']
    token_amount = data.get('token_amount')
    
    if not token_amount or token_amount <= 0:
        return jsonify({'error': 'Invalid token amount'}), 400
    
    # Calculate price (example: $2.99 per 1000 tokens)
    price_per_1k = 2.99
    total_price_cents = int((token_amount / 1000) * price_per_1k * 100)
    
    try:
        # Process payment
        payment_processor = PaymentProcessor()
        payment_result = payment_processor.process_token_purchase(
            user_id=user_id,
            token_amount=token_amount,
            price_cents=total_price_cents,
            payment_details=data.get('payment_details', {})
        )
        
        if not payment_result['success']:
            return jsonify({
                'error': 'Payment processing failed',
                'details': payment_result.get('error')
            }), 400
        
        # Create purchase record
        purchase = TokenPurchase(
            user_id=user_id,
            tokens_purchased=token_amount,
            price_paid_cents=total_price_cents,
            payment_method='stripe',
            payment_id=payment_result.get('payment_id'),
            payment_status='completed',
            purchase_reason='token_purchase',
            completed_at=datetime.utcnow()
        )
        
        db.session.add(purchase)
        
        # Add tokens to user account
        token_result = token_manager.add_tokens(user_id, token_amount, "Purchase")
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'purchase': purchase.to_dict(),
            'new_token_balance': token_result,
            'message': f'Successfully purchased {token_amount} tokens'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Token purchase failed: {str(e)}")
        return jsonify({'error': 'Token purchase failed'}), 500

@billing_bp.route('/usage-analytics', methods=['GET'])
@login_required
def get_usage_analytics():
    """Get detailed usage analytics"""
    user_id = session['user_id']
    days = request.args.get('days', 30, type=int)
    
    analytics = token_manager.get_usage_analytics(user_id, days)
    
    # Get detailed logs
    logs = TokenUsageLog.query.filter_by(user_id=user_id)\
        .filter(TokenUsageLog.created_at >= datetime.utcnow() - timedelta(days=days))\
        .order_by(TokenUsageLog.created_at.desc())\
        .limit(100).all()
    
    return jsonify({
        'success': True,
        'analytics': analytics,
        'recent_operations': [log.to_dict() for log in logs],
        'recommendations': get_usage_recommendations(analytics)
    })

@billing_bp.route('/billing-history', methods=['GET'])
@login_required
def get_billing_history():
    """Get billing history for user"""
    user_id = session['user_id']
    history = get_billing_history_for_user(user_id)
    
    return jsonify({
        'success': True,
        'billing_history': history
    })

@billing_bp.route('/invoice/<invoice_id>', methods=['GET'])
@login_required
def get_invoice(invoice_id):
    """Get specific invoice details"""
    user_id = session['user_id']
    
    # Find invoice in purchases or subscription payments
    purchase = TokenPurchase.query.filter_by(
        id=invoice_id, 
        user_id=user_id
    ).first()
    
    if purchase:
        return jsonify({
            'success': True,
            'invoice_type': 'token_purchase',
            'invoice': purchase.to_dict()
        })
    
    return jsonify({'error': 'Invoice not found'}), 404

@billing_bp.route('/webhooks/stripe', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhooks"""
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        # Verify webhook signature
        payment_processor = PaymentProcessor('stripe')
        event = payment_processor.verify_webhook(payload, sig_header)
        
        # Handle different event types
        if event['type'] == 'invoice.payment_succeeded':
            handle_successful_payment(event['data']['object'])
        elif event['type'] == 'invoice.payment_failed':
            handle_failed_payment(event['data']['object'])
        elif event['type'] == 'customer.subscription.deleted':
            handle_subscription_cancelled(event['data']['object'])
        
        return jsonify({'success': True})
        
    except Exception as e:
        current_app.logger.error(f"Webhook processing failed: {str(e)}")
        return jsonify({'error': 'Webhook processing failed'}), 400

def calculate_proration(current_plan: BillingPlan, new_plan: BillingPlan, days_remaining: int) -> Dict:
    """Calculate prorated charges for plan upgrade"""
    
    current_daily_rate = current_plan.monthly_price_cents / 30
    new_daily_rate = new_plan.monthly_price_cents / 30
    
    credit_for_unused = current_daily_rate * days_remaining
    charge_for_new = new_daily_rate * days_remaining
    
    amount_due = max(0, charge_for_new - credit_for_unused)
    
    return {
        'current_plan_credit': credit_for_unused,
        'new_plan_charge': charge_for_new,
        'amount_due': amount_due,
        'days_remaining': days_remaining
    }

def get_billing_history_for_user(user_id: int) -> List[Dict]:
    """Get comprehensive billing history"""
    
    # Get token purchases
    purchases = TokenPurchase.query.filter_by(user_id=user_id)\
        .order_by(TokenPurchase.created_at.desc()).all()
    
    # Get subscription history (would need SubscriptionPayment model for full history)
    subscription = UserSubscription.query.filter_by(user_id=user_id).first()
    
    history = []
    
    # Add purchases to history
    for purchase in purchases:
        history.append({
            'type': 'token_purchase',
            'date': purchase.created_at.isoformat(),
            'amount': purchase.price_paid_cents / 100.0,
            'description': f'{purchase.tokens_purchased} tokens purchased',
            'status': purchase.payment_status,
            'invoice_id': purchase.id
        })
    
    # Add subscription info
    if subscription:
        history.append({
            'type': 'subscription',
            'date': subscription.created_at.isoformat(),
            'amount': subscription.plan.monthly_price_cents / 100.0 if subscription.plan else 0,
            'description': f'{subscription.plan.display_name} subscription' if subscription.plan else 'Subscription',
            'status': subscription.status,
            'period_end': subscription.current_period_end.isoformat()
        })
    
    return sorted(history, key=lambda x: x['date'], reverse=True)

def get_usage_recommendations(analytics: Dict) -> List[str]:
    """Generate usage recommendations based on analytics"""
    recommendations = []
    
    if analytics.get('remaining', 0) < 100:
        recommendations.append("Vaše tokeny se vyčerpávají. Zvažte nákup dalších tokenů nebo upgrade plánu.")
    
    most_used = analytics.get('most_used_operation')
    if most_used:
        recommendations.append(f"Nejvíce používáte funkci '{most_used}'. Zvažte optimalizaci těchto operací.")
    
    avg_daily = analytics.get('average_daily_usage', 0)
    if avg_daily > 100:
        recommendations.append("Vysoké denní využití. Pro lepší hodnotu zvažte upgrade na vyšší plán.")
    
    return recommendations

def handle_successful_payment(invoice):
    """Handle successful payment webhook"""
    customer_id = invoice.get('customer')
    subscription_id = invoice.get('subscription')
    
    if subscription_id:
        subscription = UserSubscription.query.filter_by(
            stripe_subscription_id=subscription_id
        ).first()
        
        if subscription:
            # Reset tokens for new billing period
            subscription.tokens_used_this_period = 0
            subscription.current_period_start = datetime.utcnow()
            subscription.current_period_end = datetime.utcnow() + timedelta(days=30)
            
            # Update user token limit
            user = subscription.user
            user.tokens_used = 0
            user.tokens_limit = subscription.plan.monthly_token_limit
            
            db.session.commit()

def handle_failed_payment(invoice):
    """Handle failed payment webhook"""
    subscription_id = invoice.get('subscription')
    
    if subscription_id:
        subscription = UserSubscription.query.filter_by(
            stripe_subscription_id=subscription_id
        ).first()
        
        if subscription:
            # Could implement dunning management here
            # For now, just log the failure
            current_app.logger.warning(f"Payment failed for subscription {subscription.id}")

def handle_subscription_cancelled(subscription_obj):
    """Handle subscription cancellation webhook"""
    subscription_id = subscription_obj.get('id')
    
    subscription = UserSubscription.query.filter_by(
        stripe_subscription_id=subscription_id
    ).first()
    
    if subscription:
        subscription.status = 'cancelled'
        
        # Downgrade user to free plan
        user = subscription.user
        free_plan = BillingPlan.query.filter_by(name='free').first()
        if free_plan:
            user.plan = 'free'
            user.tokens_limit = free_plan.monthly_token_limit
        
        db.session.commit()