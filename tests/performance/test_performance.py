# tests/performance/test_performance.py - Performance Tests
import time
import pytest

@pytest.mark.slow
class TestPerformance:
    """Performance tests"""
    
    def test_api_response_time(self, client, authenticated_user):
        """Test API response times"""
        start_time = time.time()
        
        response = client.get('/api/projects')
        
        end_time = time.time()
        response_time = end_time - start_time
        
        assert response.status_code == 200
        assert response_time < 1.0  # Should respond within 1 second
    
    def test_ai_operation_timeout(self, client, authenticated_user):
        """Test AI operation doesn't timeout"""
        start_time = time.time()
        
        response = client.post('/api/ai/analyze-idea', json={
            'idea_text': 'A complex story with many characters and plot lines'
        })
        
        end_time = time.time()
        response_time = end_time - start_time
        
        assert response.status_code == 200
        assert response_time < 10.0  # Should complete within 10 seconds
