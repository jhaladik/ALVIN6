# tests/unit/test_api.py - API Unit Tests
class TestAuthAPI:
    """Test authentication API"""
    
    def test_login_valid_credentials(self, client, test_user):
        """Test login with valid credentials"""
        response = client.post('/api/auth/login', json={
            'email': 'test@example.com',
            'password': 'testpassword'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'user' in data
    
    def test_login_invalid_credentials(self, client, test_user):
        """Test login with invalid credentials"""
        response = client.post('/api/auth/login', json={
            'email': 'test@example.com',
            'password': 'wrongpassword'
        })
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'error' in data
    
    def test_get_current_user_authenticated(self, client, authenticated_user):
        """Test getting current user when authenticated"""
        response = client.get('/api/auth/me')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['user']['email'] == 'test@example.com'
    
    def test_get_current_user_unauthenticated(self, client):
        """Test getting current user when not authenticated"""
        response = client.get('/api/auth/me')
        
        assert response.status_code == 401

class TestProjectsAPI:
    """Test projects API"""
    
    def test_get_projects_authenticated(self, client, authenticated_user, test_project):
        """Test getting projects when authenticated"""
        response = client.get('/api/projects')
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) >= 1
        assert data[0]['title'] == 'Test Story'
    
    def test_create_project(self, client, authenticated_user):
        """Test creating new project"""
        response = client.post('/api/projects', json={
            'title': 'New Project',
            'description': 'A new project',
            'genre': 'fantasy'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['project']['title'] == 'New Project'