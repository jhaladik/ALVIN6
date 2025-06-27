# setup_claude.py - Claude API Setup Helper
import os
import requests
from getpass import getpass

def get_claude_api_key():
    """Interactive setup for Claude API key"""
    print("🔑 Claude API Key Setup")
    print("="*50)
    print()
    print("Pro získání Claude API klíče:")
    print("1. Jděte na https://console.anthropic.com/")
    print("2. Vytvořte účet nebo se přihlaste")
    print("3. Jděte na 'API Keys' v nastavení")
    print("4. Vytvořte nový API klíč")
    print("5. Zkopírujte klíč (začíná 'sk-ant-')")
    print()
    
    while True:
        api_key = getpass("Vložte váš Claude API klíč: ").strip()
        
        if not api_key:
            print("❌ API klíč nesmí být prázdný")
            continue
        
        if not api_key.startswith('sk-ant-'):
            print("❌ Claude API klíče začínají 'sk-ant-'")
            continue
        
        # Test the API key
        print("🧪 Testuji API klíč...")
        if test_api_key(api_key):
            print("✅ API klíč je platný!")
            save_to_env(api_key)
            return api_key
        else:
            print("❌ API klíč není platný. Zkuste znovu.")

def test_api_key(api_key):
    """Test if Claude API key is valid"""
    try:
        from anthropic import Anthropic
        
        client = Anthropic(api_key=api_key)
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=10,
            messages=[{"role": "user", "content": "Test"}]
        )
        
        return len(response.content) > 0
        
    except Exception as e:
        print(f"Chyba při testování: {str(e)}")
        return False

def save_to_env(api_key):
    """Save API key to .env file"""
    env_file = '.env'
    
    # Read existing .env
    env_lines = []
    if os.path.exists(env_file):
        with open(env_file, 'r', encoding='utf-8') as f:
            env_lines = f.readlines()
    
    # Update or add ANTHROPIC_API_KEY
    api_key_line = f"ANTHROPIC_API_KEY={api_key}\n"
    found = False
    
    for i, line in enumerate(env_lines):
        if line.startswith('ANTHROPIC_API_KEY='):
            env_lines[i] = api_key_line
            found = True
            break
    
    if not found:
        env_lines.append(api_key_line)
    
    # Write back to .env
    with open(env_file, 'w', encoding='utf-8') as f:
        f.writelines(env_lines)
    
    print(f"💾 API klíč uložen do {env_file}")

def check_anthropic_package():
    """Check if anthropic package is installed"""
    try:
        import anthropic
        print("✅ Anthropic package je nainstalován")
        return True
    except ImportError:
        print("❌ Anthropic package není nainstalován")
        print("Spusťte: pip install anthropic")
        return False

if __name__ == '__main__':
    print("🎭 StoryForge AI - Claude API Setup")
    print("="*40)
    
    if not check_anthropic_package():
        exit(1)
    
    api_key = get_claude_api_key()
    
    print("\n🎉 Setup dokončen!")
    print("Nyní můžete spustit aplikaci s Claude AI:")
    print("python run.py")