# test_api.py - Rychlý test script pro ověření API
import requests
import json

def test_storyforge_api():
    """Test základní funkcionalita API"""
    base_url = 'http://localhost:5000'
    
    print("🧪 Testování StoryForge AI API...")
    
    # Test 1: Health check
    print("\n1. Health Check...")
    try:
        response = requests.get(f'{base_url}/health')
        print(f"✅ Health: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ Health Error: {e}")
    
    # Test 2: API Info
    print("\n2. API Info...")
    try:
        response = requests.get(f'{base_url}/api')
        print(f"✅ API Info: {response.status_code}")
        print(f"   Service: {response.json()['service']}")
    except Exception as e:
        print(f"❌ API Info Error: {e}")
    
    # Test 3: Login
    print("\n3. Login Test...")
    session = requests.Session()
    try:
        login_data = {
            'email': 'demo@storyforge.ai',
            'password': 'demo123'
        }
        response = session.post(f'{base_url}/api/auth/login', json=login_data)
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ Login Success: {user_data['user']['username']} ({user_data['user']['plan']})")
            
            # Test 4: Get Projects
            print("\n4. Get Projects...")
            response = session.get(f'{base_url}/api/projects')
            if response.status_code == 200:
                projects = response.json()
                print(f"✅ Projects: Found {len(projects)} projects")
                for project in projects:
                    print(f"   - {project['title']} ({project['current_phase']})")
            else:
                print(f"❌ Projects Error: {response.status_code}")
                
        else:
            print(f"❌ Login Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Login Error: {e}")
    
    # Test 5: Create Scene (requires login)
    if 'user_data' in locals():
        print("\n5. Create Scene Test...")
        try:
            # Get first project
            projects_response = session.get(f'{base_url}/api/projects')
            if projects_response.status_code == 200:
                projects = projects_response.json()
                if projects:
                    project_id = projects[0]['id']
                    
                    scene_data = {
                        'project_id': project_id,
                        'title': 'Test Scene',
                        'description': 'Sarah objeví tajemnou knihu v knihovně a Pavel jí pomůže.',
                        'scene_type': 'development'
                    }
                    
                    response = session.post(f'{base_url}/api/scenes', json=scene_data)
                    if response.status_code == 200:
                        scene = response.json()
                        print(f"✅ Scene Created: {scene['scene']['title']}")
                    else:
                        print(f"❌ Scene Error: {response.status_code} - {response.text}")
                else:
                    print("⚠️  No projects found for scene test")
        except Exception as e:
            print(f"❌ Scene Error: {e}")
    
    print("\n🎉 API Test dokončen!")

if __name__ == '__main__':
    test_storyforge_api()