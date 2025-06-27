# test_app.py - Quick verification script for StoryForge AI (Windows compatible)
import requests
import json
import sys

BASE_URL = "http://localhost:5000"

def test_health_check():
    """Test if server is running"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Server not running or not accessible")
        return False

def test_api_info():
    """Test API info endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/api")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API info retrieved: {data['service']}")
            return True
        else:
            print(f"❌ API info failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API info error: {str(e)}")
        return False

def test_demo_login():
    """Test demo user login"""
    try:
        session = requests.Session()
        login_data = {
            "email": "demo@storyforge.ai",
            "password": "demo123"
        }
        
        response = session.post(f"{BASE_URL}/api/auth/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ Demo login successful: {data['user']['username']}")
                return session, data['user']
            else:
                print(f"❌ Demo login failed: {data.get('error')}")
                return None, None
        else:
            print(f"❌ Demo login HTTP error: {response.status_code}")
            return None, None
    except Exception as e:
        print(f"❌ Demo login error: {str(e)}")
        return None, None

def test_current_user(session):
    """Test getting current user info"""
    try:
        response = session.get(f"{BASE_URL}/api/auth/me")
        if response.status_code == 200:
            data = response.json()
            user = data['user']
            print(f"✅ Current user: {user['username']} ({user['plan']}) - {user['tokens_used']}/{user['tokens_limit']} tokens")
            return True
        else:
            print(f"❌ Current user failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Current user error: {str(e)}")
        return False

def test_projects(session):
    """Test getting projects"""
    try:
        response = session.get(f"{BASE_URL}/api/projects")
        if response.status_code == 200:
            projects = response.json()
            print(f"✅ Projects retrieved: {len(projects)} projects found")
            if projects:
                print(f"   Sample project: {projects[0].get('title', 'Untitled')}")
            return True
        else:
            print(f"❌ Projects failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Projects error: {str(e)}")
        return False

def test_ai_idea_analysis(session):
    """Test AI idea analysis"""
    try:
        idea_data = {
            "idea_text": "A young detective discovers a mysterious coded letter in her grandmother's attic",
            "story_intent": "mystery"
        }
        
        response = session.post(f"{BASE_URL}/api/ai/analyze-idea", json=idea_data)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                analysis = data['analysis']
                genre = analysis.get('story_assessment', {}).get('genre', 'unknown')
                print(f"✅ AI analysis successful: Genre identified as '{genre}'")
                return True
            else:
                print(f"❌ AI analysis failed: {data.get('error')}")
                return False
        elif response.status_code == 402:
            print("⚠️ AI analysis blocked: Insufficient tokens (this is expected behavior)")
            return True
        else:
            print(f"❌ AI analysis HTTP error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ AI analysis error: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting StoryForge AI verification tests...\n")
    
    # Test 1: Health check
    if not test_health_check():
        print("\n❌ Server is not running. Please start the server with 'python run.py'")
        sys.exit(1)
    
    # Test 2: API info
    test_api_info()
    
    # Test 3: Demo login
    session, user = test_demo_login()
    if not session:
        print("\n❌ Cannot proceed without authentication")
        sys.exit(1)
    
    # Test 4: Current user
    test_current_user(session)
    
    # Test 5: Projects
    test_projects(session)
    
    # Test 6: AI functionality
    test_ai_idea_analysis(session)
    
    print("\n🎉 All core tests completed!")
    print("\n📋 Next steps:")
    print("1. Open your browser and go to http://localhost:5000")
    print("2. Login with: demo@storyforge.ai / demo123")
    print("3. Try creating a new story in the 'Nápad' (Idea) phase")
    print("4. Explore the demo project 'Tajemství babičky Anny'")

if __name__ == "__main__":
    main()