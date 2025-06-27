# test_claude_fix.py - Test script for Claude API fix
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_anthropic_versions():
    """Test different Anthropic SDK versions and compatibility"""
    print("🧪 Testing Anthropic SDK compatibility...")
    
    try:
        import anthropic
        print(f"✅ Anthropic package version: {anthropic.__version__}")
        
        # Test different initialization methods
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            print("⚠️  No ANTHROPIC_API_KEY found, testing simulation mode only")
            test_simulation()
            return
        
        print(f"✅ API key present: {api_key[:8]}...")
        
        # Test 1: Basic initialization
        try:
            client = anthropic.Anthropic(api_key=api_key)
            print("✅ Basic Anthropic client initialization successful")
        except Exception as e:
            print(f"❌ Basic initialization failed: {e}")
            test_simulation()
            return
        
        # Test 2: Simple API call
        try:
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=50,
                system="Odpovídejte v češtině.",
                messages=[{
                    "role": "user", 
                    "content": "Řekněte 'Test Claude API úspěšný!'"
                }]
            )
            
            response_text = response.content[0].text
            print(f"✅ API call successful: {response_text}")
            
        except Exception as e:
            print(f"❌ API call failed: {e}")
            test_simulation()
            return
        
        print("🎉 Claude API is fully functional!")
        
    except ImportError as e:
        print(f"❌ Anthropic package not installed: {e}")
        print("Install with: pip install anthropic==0.25.1")
        test_simulation()

def test_simulation():
    """Test simulation mode"""
    print("\n🎭 Testing simulation mode...")
    
    try:
        # Import our fixed client
        sys.path.append('.')
        from app.services.claude_api import ClaudeAPIClient
        
        client = ClaudeAPIClient()
        print(f"✅ Client initialized (simulation mode: {client.simulation_mode})")
        
        # Test analysis
        result = client._make_request("Analyzuj tuto scénu: Sarah najde dopis.")
        print(f"✅ Analysis test: {len(result)} characters returned")
        
        # Test connection
        status = client.test_connection()
        print(f"✅ Connection test: {status['status']}")
        
        print("🎉 Simulation mode is working!")
        
    except Exception as e:
        print(f"❌ Simulation test failed: {e}")

def fix_anthropic_version():
    """Install compatible Anthropic version"""
    print("🔧 Installing compatible Anthropic version...")
    
    import subprocess
    import sys
    
    try:
        # Uninstall current version
        subprocess.check_call([sys.executable, '-m', 'pip', 'uninstall', 'anthropic', '-y'])
        
        # Install compatible version
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'anthropic==0.25.1'])
        
        print("✅ Anthropic 0.25.1 installed successfully")
        print("🔄 Please restart your Flask application")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Installation failed: {e}")
        print("Try manually: pip install anthropic==0.25.1")

if __name__ == '__main__':
    print("🎭 StoryForge AI - Claude API Compatibility Test\n")
    
    # Check current status
    test_anthropic_versions()
    
    # Ask user if they want to fix version
    print("\n" + "="*50)
    response = input("Do you want to install compatible Anthropic version? (y/n): ")
    
    if response.lower() in ['y', 'yes']:
        fix_anthropic_version()
    else:
        print("💡 Tip: Application will run in simulation mode if Claude API fails")