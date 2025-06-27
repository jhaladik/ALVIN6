# tests/unit/test_ai_services.py - AI Services Tests
class TestTokenManager:
    """Test token management"""
    
    def test_create_operation(self):
        """Test creating token operation"""
        from app.services.token_manager import TokenOperation
        
        operation = TokenOperation(
            operation_type='analyze_idea',
            user_id=1,
            input_tokens=100,
            output_tokens=50
        )
        
        assert operation.operation_type == 'analyze_idea'
        assert operation.total_cost > 0
    
    def test_check_balance_sufficient(self, app, test_user):
        """Test balance check with sufficient tokens"""
        with app.app_context():
            balance_check = token_manager.check_balance(test_user.id, 50)
            
            assert balance_check['allowed'] is True
    
    def test_check_balance_insufficient(self, app, test_user):
        """Test balance check with insufficient tokens"""
        with app.app_context():
            balance_check = token_manager.check_balance(test_user.id, 15000)
            
            assert balance_check['allowed'] is False
            assert 'deficit' in balance_check

class TestAIAnalyzer:
    """Test AI analyzer"""
    
    def test_analyze_idea_simulation(self, app):
        """Test idea analysis in simulation mode"""
        from app.services.ai_analyzer import AIAnalyzer
        
        with app.app_context():
            analyzer = AIAnalyzer()
            result = analyzer.analyze_idea("A detective finds a mysterious letter")
            
            assert 'story_assessment' in result
            assert 'extracted_objects' in result
            assert 'first_scene_suggestion' in result