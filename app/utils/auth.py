# app/utils/auth.py - ENHANCED Authentication with Token Management
from functools import wraps
from flask import session, jsonify, request, current_app
from app.models import User, TokenUsageLog, UserSubscription
from app.services.token_manager import token_manager, TokenOperation
from app import db
from datetime import datetime
import time

def login_required(f):
    """Enhanced login requirement decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Check if user still exists and is active
        user = User.query.get(session['user_id'])
        if not user or not user.is_active:
            session.pop('user_id', None)
            return jsonify({'error': 'User account not found or inactive'}), 401
        
        return f(*args, **kwargs)
    return decorated_function

def enhanced_token_check(operation_type: str, estimate_input_text: str = ""):
    """Enhanced token checking with precise cost estimation"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            user_id = session['user_id']
            
            # Get cost estimate
            cost_estimate = token_manager.get_cost_estimate(operation_type, estimate_input_text)
            estimated_cost = cost_estimate['estimated_total_cost']
            
            # Check if user has sufficient tokens
            balance_check = token_manager.check_balance(user_id, estimated_cost)
            
            if not balance_check['allowed']:
                return jsonify({
                    'error': 'Insufficient tokens',
                    'required_tokens': estimated_cost,
                    'remaining_tokens': balance_check.get('remaining', 0),
                    'cost_estimate': cost_estimate,
                    'upgrade_suggestions': _get_upgrade_suggestions(user_id, estimated_cost)
                }), 402  # Payment Required
            
            # Store the operation details for later execution
            request.token_operation_type = operation_type
            request.token_cost_estimate = cost_estimate
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def execute_token_operation(operation_type: str, user_id: int, input_tokens: int = 0, 
                          output_tokens: int = 0, metadata: dict = None,
                          project_id: str = None, scene_id: int = None,
                          ai_model: str = None, response_time_ms: int = None):
    """Execute and log a token operation"""
    
    # Create the operation
    operation = token_manager.create_operation(
        operation_type=operation_type,
        user_id=user_id,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        metadata=metadata
    )
    
    # Execute the operation
    result = token_manager.execute_operation(operation)
    
    if result['success']:
        # Log to database
        log_entry = TokenUsageLog(
            user_id=user_id,
            operation_type=operation_type,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_cost=operation.total_cost,
            multiplier=operation.multiplier,
            project_id=project_id,
            scene_id=scene_id,
            metadata=metadata or {},
            ai_model_used=ai_model,
            response_time_ms=response_time_ms,
            billable=True,
            created_at=operation.timestamp
        )
        
        db.session.add(log_entry)
        
        # Update user's subscription token usage if applicable
        subscription = UserSubscription.query.filter_by(user_id=user_id).first()
        if subscription:
            subscription.tokens_used_this_period += operation.total_cost
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to log token usage: {str(e)}")
    
    return result

def track_ai_operation(operation_type: str):
    """Decorator to track AI operations with precise token measurement"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            user_id = session['user_id']
            start_time = time.time()
            
            # Get request data for input token estimation
            request_data = request.get_json() or {}
            input_text = ""
            
            # Extract text from common fields for token counting
            for field in ['idea_text', 'description', 'content', 'prompt']:
                if field in request_data:
                    input_text += str(request_data[field]) + " "
            
            # Estimate input tokens (will be refined with actual API response)
            estimated_input_tokens = len(input_text.split()) * 1.3
            
            # Execute the original function
            try:
                response = f(*args, **kwargs)
                
                # Calculate response time
                response_time_ms = int((time.time() - start_time) * 1000)
                
                # Try to extract actual token usage from AI API response
                actual_input_tokens = estimated_input_tokens
                actual_output_tokens = 50  # Default estimate
                ai_model = "claude-3-5-sonnet"  # Default
                
                # If response contains AI operation details, extract them
                if hasattr(response, 'get_json'):
                    response_data = response.get_json()
                    if response_data and 'ai_metadata' in response_data:
                        ai_meta = response_data['ai_metadata']
                        actual_input_tokens = ai_meta.get('input_tokens', actual_input_tokens)
                        actual_output_tokens = ai_meta.get('output_tokens', actual_output_tokens)
                        ai_model = ai_meta.get('model', ai_model)
                
                # Execute token operation
                token_result = execute_token_operation(
                    operation_type=operation_type,
                    user_id=user_id,
                    input_tokens=int(actual_input_tokens),
                    output_tokens=int(actual_output_tokens),
                    metadata={
                        'request_size': len(input_text),
                        'response_time_ms': response_time_ms,
                        'endpoint': request.endpoint
                    },
                    project_id=request_data.get('project_id'),
                    scene_id=request_data.get('scene_id'),
                    ai_model=ai_model,
                    response_time_ms=response_time_ms
                )
                
                # Add token usage info to response if it's JSON
                if hasattr(response, 'get_json') and response.get_json():
                    response_data = response.get_json()
                    response_data['token_usage'] = {
                        'operation_type': operation_type,
                        'tokens_used': token_result.get('tokens_used', 0),
                        'remaining_tokens': token_result.get('remaining_tokens', 0),
                        'input_tokens': int(actual_input_tokens),
                        'output_tokens': int(actual_output_tokens)
                    }
                    response.data = jsonify(response_data).data
                
                return response
                
            except Exception as e:
                # Log failed operation (no tokens charged)
                current_app.logger.error(f"AI operation {operation_type} failed for user {user_id}: {str(e)}")
                raise e
        
        return decorated_function
    return decorator

def subscription_required(feature: str = None):
    """Check if user has valid subscription for feature"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            user_id = session['user_id']
            subscription = UserSubscription.query.filter_by(user_id=user_id).first()
            
            if not subscription or subscription.status != 'active':
                return jsonify({
                    'error': 'Active subscription required',
                    'feature': feature,
                    'upgrade_url': '/billing/upgrade'
                }), 402
            
            # Check if subscription covers the feature
            if feature and subscription.plan:
                plan_features = subscription.plan.features or []
                if feature not in plan_features:
                    return jsonify({
                        'error': f'Feature "{feature}" not available in your plan',
                        'current_plan': subscription.plan.name,
                        'upgrade_url': '/billing/upgrade'
                    }), 402
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def collaboration_permission_required(permission: str):
    """Check collaboration permissions for project"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            user_id = session['user_id']
            project_id = kwargs.get('project_id') or request.get_json().get('project_id')
            
            if not project_id:
                return jsonify({'error': 'Project ID required'}), 400
            
            # Check if user is project owner
            from app.models import Project, ProjectCollaborator
            project = Project.query.filter_by(id=project_id, user_id=user_id).first()
            
            if project:
                # Owner has all permissions
                return f(*args, **kwargs)
            
            # Check collaboration permissions
            collaborator = ProjectCollaborator.query.filter_by(
                project_id=project_id, 
                user_id=user_id,
                status='active'
            ).first()
            
            if not collaborator:
                return jsonify({'error': 'Access denied to project'}), 403
            
            # Check specific permission
            user_permissions = collaborator.permissions or {}
            if permission not in user_permissions or not user_permissions[permission]:
                return jsonify({
                    'error': f'Permission "{permission}" required',
                    'user_role': collaborator.role
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def rate_limit(requests_per_minute: int = 60):
    """Rate limiting decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Simple in-memory rate limiting (use Redis in production)
            user_id = session.get('user_id', 'anonymous')
            current_time = time.time()
            
            # This is a simplified implementation
            # In production, use Redis with sliding window
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def _get_upgrade_suggestions(user_id: int, required_tokens: int) -> dict:
    """Get upgrade suggestions for user"""
    from app.models import BillingPlan
    
    plans = BillingPlan.query.filter_by(is_active=True, is_public=True).all()
    suggestions = []
    
    for plan in plans:
        if plan.monthly_token_limit >= required_tokens:
            suggestions.append({
                'plan_name': plan.display_name,
                'monthly_tokens': plan.monthly_token_limit,
                'monthly_price': plan.monthly_price_cents / 100.0,
                'upgrade_url': f'/billing/upgrade/{plan.name}'
            })
    
    return {
        'available_plans': suggestions,
        'token_purchase_url': '/billing/buy-tokens',
        'tokens_needed': required_tokens
    }

# Backwards compatibility aliases
check_tokens = enhanced_token_check
use_tokens = execute_token_operation