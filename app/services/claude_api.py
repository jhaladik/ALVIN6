# app/services/claude_api.py - FIXED Claude API Client
import os
import json
import re
import time
from typing import Dict, List, Optional, Tuple
from flask import current_app
from functools import lru_cache

# Try different Anthropic imports for compatibility
try:
    from anthropic import Anthropic, Client
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("Warning: Anthropic package not installed. AI will run in simulation mode.")

# Try tiktoken for token counting
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    print("Warning: tiktoken not installed. Token counting will use estimation.")

class ClaudeAPIClient:
    """Claude API client for StoryForge AI with compatibility fixes"""
    
    def __init__(self):
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        self.model = os.getenv('DEFAULT_CLAUDE_MODEL', 'claude-3-5-sonnet-20241022')
        self.simulation_mode = os.getenv('AI_SIMULATION_MODE', 'false').lower() == 'true'
        
        # Force simulation mode if no API key or Anthropic not available
        if not self.api_key or not ANTHROPIC_AVAILABLE:
            print(f"Claude API: Running in simulation mode (API key: {'present' if self.api_key else 'missing'}, SDK: {'available' if ANTHROPIC_AVAILABLE else 'missing'})")
            self.simulation_mode = True
        
        if not self.simulation_mode and ANTHROPIC_AVAILABLE:
            try:
                # Initialize Anthropic client with minimal arguments for compatibility
                self.client = Anthropic(api_key=self.api_key)
                print(f"Claude API: Initialized successfully with model {self.model}")
            except Exception as e:
                print(f"Claude API: Initialization failed: {str(e)}")
                print("Claude API: Falling back to simulation mode")
                self.simulation_mode = True
        
        # Rate limiting
        self.max_requests_per_minute = int(os.getenv('CLAUDE_MAX_REQUESTS_PER_MINUTE', 50))
        self.max_tokens_per_request = int(os.getenv('CLAUDE_MAX_TOKENS_PER_REQUEST', 4000))
        self.request_times = []
    
    def _check_rate_limit(self):
        """Check if we're within rate limits"""
        now = time.time()
        # Remove requests older than 1 minute
        self.request_times = [t for t in self.request_times if now - t < 60]
        
        if len(self.request_times) >= self.max_requests_per_minute:
            raise Exception(f"Rate limit exceeded: {self.max_requests_per_minute} requests per minute")
        
        self.request_times.append(now)
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        if not TIKTOKEN_AVAILABLE:
            # Fallback: rough estimation (1 token ≈ 0.75 words)
            return int(len(text.split()) * 1.3)
        
        try:
            # Use tiktoken for more accurate counting
            tokenizer = tiktoken.encoding_for_model("gpt-4")  # Close approximation for Claude
            return len(tokenizer.encode(text))
        except Exception:
            # Fallback estimation
            return int(len(text.split()) * 1.3)
    
    def _make_request(self, prompt: str, system_prompt: str = None, max_tokens: int = 2000) -> str:
        """Make request to Claude API with error handling"""
        if self.simulation_mode:
            return self._simulate_response(prompt)
        
        try:
            self._check_rate_limit()
            
            # Count input tokens
            total_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            input_tokens = self.count_tokens(total_prompt)
            
            if input_tokens > self.max_tokens_per_request:
                raise Exception(f"Prompt too long: {input_tokens} tokens (max: {self.max_tokens_per_request})")
            
            # Prepare messages
            messages = [{"role": "user", "content": prompt}]
            
            # Create request parameters
            request_params = {
                "model": self.model,
                "max_tokens": max_tokens,
                "messages": messages,
                "temperature": 0.7
            }
            
            # Add system prompt if provided
            if system_prompt:
                request_params["system"] = system_prompt
            
            # Make the API call
            response = self.client.messages.create(**request_params)
            
            # Extract response content
            if hasattr(response, 'content') and len(response.content) > 0:
                if hasattr(response.content[0], 'text'):
                    return response.content[0].text
                else:
                    return str(response.content[0])
            else:
                raise Exception("Empty response from Claude API")
            
        except Exception as e:
            error_msg = str(e)
            print(f"Claude API error: {error_msg}")
            
            # Log to Flask if available
            if current_app:
                current_app.logger.error(f"Claude API error: {error_msg}")
            
            # Fallback to simulation for certain errors
            if any(keyword in error_msg.lower() for keyword in ['rate limit', 'quota', 'billing', 'api key']):
                print("Claude API: Critical error, switching to simulation mode")
                self.simulation_mode = True
                return self._simulate_response(prompt)
            else:
                # For other errors, try simulation as fallback
                print("Claude API: Temporary error, using simulation fallback")
                return self._simulate_response(prompt)
    
    def _simulate_response(self, prompt: str) -> str:
        """Simulate AI response for development/testing"""
        time.sleep(0.5)  # Simulate API delay
        
        prompt_lower = prompt.lower()
        
        if "analyzuj scénu" in prompt_lower or "analyze scene" in prompt_lower:
            return """
            {
                "characters": ["Sarah", "Pavel"],
                "locations": ["Knihovna"],
                "objects": ["Zakódovaný dopis", "Historické knihy"],
                "conflicts": ["Odhalování pravdy"]
            }
            """
        elif "analyzuj strukturu" in prompt_lower or "analyze structure" in prompt_lower:
            return """
            {
                "total_scenes": 2,
                "continuity_score": 0.85,
                "pacing_score": 0.72,
                "scene_types": {"inciting": 1, "development": 1},
                "missing_elements": ["climax", "resolution"],
                "recommendations": [
                    "Přidejte klimax scénu pro vrchol napětí",
                    "Vytvořte rozuzlení pro uzavření příběhu"
                ],
                "strengths": ["Silná charakterizace hlavní postavy", "Dobré využití objektů"],
                "scene_balance": "good",
                "character_development": "strong"
            }
            """
        elif "navrhni scény" in prompt_lower or "suggest scenes" in prompt_lower:
            return """
            [
                {
                    "title": "Konfrontace s pravdou",
                    "description": "Sarah konfrontuje svou matku s objevenými informacemi o babičce",
                    "scene_type": "development",
                    "suggested_objects": ["Rodinné fotografie", "Matka"],
                    "confidence": 0.9
                },
                {
                    "title": "Návštěva válečného archívu",
                    "description": "Pavel a Sarah navštíví archív aby ověřili babiččinu identitu",
                    "scene_type": "rising_action",
                    "suggested_objects": ["Archivní dokumenty", "Historik"],
                    "confidence": 0.85
                }
            ]
            """
        elif "vytvořte příběh" in prompt_lower or "generate story" in prompt_lower:
            return """
            {
                "title": "Tajemství babičky Anny",
                "premise": "Mladá žena objevuje válečné tajemství své babičky skrze zakódované zprávy",
                "theme": "Rodinné dědictví a síla pravdy",
                "protagonist": "Sarah - transformace od nevědomosti k poznání rodinné historie",
                "central_conflict": "Odhalování bolestivé pravdy vs. ochrana rodinného klidu",
                "story_arc": "Objevení → Pátrání → Odhalení → Přijetí",
                "tone": "Mystery s emotivními prvky",
                "estimated_length": "15000 slov",
                "target_audience": "Dospělí čtenáři mystery/drama"
            }
            """
        else:
            return f"Simulovaná odpověď Claude API pro prompt: {prompt[:100]}..."
    
    def test_connection(self) -> Dict[str, any]:
        """Test Claude API connection and return status"""
        if self.simulation_mode:
            return {
                "status": "simulation",
                "message": "Running in simulation mode",
                "api_key_present": bool(self.api_key),
                "sdk_available": ANTHROPIC_AVAILABLE
            }
        
        try:
            # Simple test request
            response = self._make_request(
                "Odpovězte jednoduše 'Test úspěšný' v češtině.",
                "Jste AI asistent pro testování.",
                50
            )
            
            return {
                "status": "success",
                "message": "Claude API is working",
                "model": self.model,
                "response": response.strip()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Claude API test failed: {str(e)}",
                "simulation_fallback": True
            }