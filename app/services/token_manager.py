# app/services/token_manager.py - Enhanced Token Management
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from flask import current_app
from app import db
from app.models import User
import json

class TokenOperation:
    """Represents a token usage operation"""
    
    # Operation types with their base token costs
    OPERATION_COSTS = {
        'analyze_idea': 8,
        'create_project_from_idea': 12,
        'analyze_structure': 15,
        'suggest_scenes': 10,
        'generate_story': 25,
        'ai_critics': 20,
        'create_scene': 5,
        'dialog_critique': 8,
        'pacing_critique': 12,
        'genre_expert': 10,
        'plot_hole_detection': 15,
        'character_arc_analysis': 12,
        'conflict_escalation': 8,
        'collaboration_sync': 2,
        'real_time_suggestion': 3,
    }
    
    def __init__(self, operation_type: str, user_id: int, 
                 input_tokens: int = 0, output_tokens: int = 0,
                 multiplier: float = 1.0, metadata: Dict = None):
        self.operation_type = operation_type
        self.user_id = user_id
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.multiplier = multiplier
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow()
        
        # Calculate total cost
        base_cost = self.OPERATION_COSTS.get(operation_type, 5)
        token_cost = (input_tokens * 0.01) + (output_tokens * 0.03)  # Different rates for input/output
        self.total_cost = int((base_cost + token_cost) * multiplier)

class TokenManager:
    """Advanced token management system"""
    
    def __init__(self):
        self.operations_log = []
    
    def create_operation(self, operation_type: str, user_id: int, 
                        input_tokens: int = 0, output_tokens: int = 0,
                        multiplier: float = 1.0, metadata: Dict = None) -> TokenOperation:
        """Create a new token operation"""
        return TokenOperation(operation_type, user_id, input_tokens, 
                            output_tokens, multiplier, metadata)
    
    def check_balance(self, user_id: int, required_tokens: int) -> Dict:
        """Check if user has sufficient token balance"""
        user = User.query.get(user_id)
        if not user:
            return {'allowed': False, 'reason': 'User not found'}
        
        remaining = user.tokens_limit - user.tokens_used
        
        if remaining < required_tokens:
            return {
                'allowed': False,
                'reason': 'Insufficient tokens',
                'required': required_tokens,
                'remaining': remaining,
                'deficit': required_tokens - remaining
            }
        
        return {
            'allowed': True,
            'remaining_after': remaining - required_tokens,
            'percentage_used': ((user.tokens_used + required_tokens) / user.tokens_limit) * 100
        }
    
    def execute_operation(self, operation: TokenOperation) -> Dict:
        """Execute token operation and update user balance"""
        # Check balance first
        balance_check = self.check_balance(operation.user_id, operation.total_cost)
        if not balance_check['allowed']:
            return {
                'success': False,
                'error': balance_check['reason'],
                'details': balance_check
            }
        
        # Deduct tokens
        user = User.query.get(operation.user_id)
        user.tokens_used += operation.total_cost
        
        # Log the operation
        self._log_operation(operation)
        
        try:
            db.session.commit()
            return {
                'success': True,
                'tokens_used': operation.total_cost,
                'remaining_tokens': user.tokens_limit - user.tokens_used,
                'operation_id': len(self.operations_log)
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': f'Database error: {str(e)}'
            }
    
    def _log_operation(self, operation: TokenOperation):
        """Log token operation for analytics"""
        log_entry = {
            'id': len(self.operations_log) + 1,
            'timestamp': operation.timestamp.isoformat(),
            'user_id': operation.user_id,
            'operation_type': operation.operation_type,
            'input_tokens': operation.input_tokens,
            'output_tokens': operation.output_tokens,
            'total_cost': operation.total_cost,
            'multiplier': operation.multiplier,
            'operation_metadata': operation.metadata
        }
        
        self.operations_log.append(log_entry)
        
        # Store in database (we'll add TokenUsageLog model)
        try:
            # This would use a TokenUsageLog model if we add it
            current_app.logger.info(f"Token operation: {json.dumps(log_entry)}")
        except:
            print(f"Token operation logged: {log_entry}")
    
    def get_usage_analytics(self, user_id: int, days: int = 30) -> Dict:
        """Get token usage analytics for user"""
        user = User.query.get(user_id)
        if not user:
            return {'error': 'User not found'}
        
        # Filter operations for this user in the time period
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        user_operations = [
            op for op in self.operations_log 
            if op['user_id'] == user_id and 
            datetime.fromisoformat(op['timestamp']) > cutoff_date
        ]
        
        # Calculate analytics
        total_used = sum(op['total_cost'] for op in user_operations)
        operations_by_type = {}
        daily_usage = {}
        
        for op in user_operations:
            # By operation type
            op_type = op['operation_type']
            if op_type not in operations_by_type:
                operations_by_type[op_type] = {'count': 0, 'tokens': 0}
            operations_by_type[op_type]['count'] += 1
            operations_by_type[op_type]['tokens'] += op['total_cost']
            
            # By day
            day = datetime.fromisoformat(op['timestamp']).date().isoformat()
            if day not in daily_usage:
                daily_usage[day] = 0
            daily_usage[day] += op['total_cost']
        
        return {
            'user_plan': user.plan,
            'total_limit': user.tokens_limit,
            'total_used_lifetime': user.tokens_used,
            'used_last_30_days': total_used,
            'remaining': user.tokens_limit - user.tokens_used,
            'operations_by_type': operations_by_type,
            'daily_usage': daily_usage,
            'most_used_operation': max(operations_by_type.items(), 
                                     key=lambda x: x[1]['tokens'])[0] if operations_by_type else None,
            'average_daily_usage': total_used / min(days, len(daily_usage)) if daily_usage else 0
        }
    
    def get_cost_estimate(self, operation_type: str, input_text: str = "") -> Dict:
        """Estimate token cost for an operation"""
        base_cost = TokenOperation.OPERATION_COSTS.get(operation_type, 5)
        
        # Estimate input tokens (rough approximation)
        estimated_input_tokens = len(input_text.split()) * 1.3 if input_text else 0
        estimated_output_tokens = base_cost * 10  # Rough estimate
        
        token_cost = (estimated_input_tokens * 0.01) + (estimated_output_tokens * 0.03)
        total_estimate = int(base_cost + token_cost)
        
        return {
            'operation_type': operation_type,
            'base_cost': base_cost,
            'estimated_input_tokens': int(estimated_input_tokens),
            'estimated_output_tokens': estimated_output_tokens,
            'estimated_total_cost': total_estimate,
            'breakdown': {
                'base_operation': base_cost,
                'input_tokens': estimated_input_tokens * 0.01,
                'output_tokens': estimated_output_tokens * 0.03
            }
        }
    
    def add_tokens(self, user_id: int, amount: int, reason: str = "Purchase") -> Dict:
        """Add tokens to user account (for purchases/bonuses)"""
        user = User.query.get(user_id)
        if not user:
            return {'success': False, 'error': 'User not found'}
        
        # For purchased tokens, we increase the limit instead of reducing used tokens
        if reason == "Purchase":
            user.tokens_limit += amount
        else:
            # For bonuses/refunds, reduce used tokens (but not below 0)
            user.tokens_used = max(0, user.tokens_used - amount)
        
        # Log the addition
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': user_id,
            'operation_type': 'token_addition',
            'amount': amount,
            'reason': reason,
            'new_limit': user.tokens_limit,
            'new_used': user.tokens_used
        }
        self.operations_log.append(log_entry)
        
        try:
            db.session.commit()
            return {
                'success': True,
                'tokens_added': amount,
                'new_limit': user.tokens_limit,
                'new_used': user.tokens_used,
                'remaining': user.tokens_limit - user.tokens_used
            }
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    def get_plan_limits(self) -> Dict:
        """Get token limits for different plans"""
        return {
            'free': {
                'monthly_limit': 1000,
                'features': ['Basic AI analysis', 'Limited scenes'],
                'cost_per_1k_tokens': 0  # Free
            },
            'pro': {
                'monthly_limit': 10000,
                'features': ['Full AI suite', 'Unlimited scenes', 'Basic collaboration'],
                'cost_per_1k_tokens': 2.99
            },
            'enterprise': {
                'monthly_limit': 50000,
                'features': ['All features', 'Priority support', 'Advanced collaboration'],
                'cost_per_1k_tokens': 1.99
            }
        }

# Global token manager instance
token_manager = TokenManager()