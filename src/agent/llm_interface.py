"""
Groq LLM interface for SQL generation.
Provides chat completion with streaming support.
"""

import os
import json
import requests
from typing import Optional, Dict, Any, List
from datetime import datetime


class GroqLLM:
    """Interface to Groq's fast inference API."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.1-8b-instant"):
        """
        Initialize Groq LLM interface.
        
        Args:
            api_key: Groq API key (or set GROQ_API_KEY env var)
            model: Model to use (default: llama-3.1-8b-instant)
                   Options: llama-3.1-8b-instant, llama-3.3-70b-versatile, mixtral-8x7b-32768
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("Groq API key required. Set GROQ_API_KEY env var or pass api_key parameter")
        
        self.model = model
        self.base_url = "https://api.groq.com/openai/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        self.conversation_history: List[Dict[str, str]] = []
    
    def chat(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.1,
        max_tokens: int = 2048,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Send chat completion request to Groq.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0.0-2.0, lower = more deterministic)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream response
            
        Returns:
            Response dict with 'content', 'model', 'tokens', etc.
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Extract relevant info
            return {
                "content": result["choices"][0]["message"]["content"],
                "model": result["model"],
                "tokens": {
                    "prompt": result["usage"]["prompt_tokens"],
                    "completion": result["usage"]["completion_tokens"],
                    "total": result["usage"]["total_tokens"]
                },
                "finish_reason": result["choices"][0]["finish_reason"],
                "timestamp": datetime.now().isoformat()
            }
            
        except requests.exceptions.RequestException as e:
            error_details = str(e)
            # Try to extract more details from response
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_json = e.response.json()
                    error_details = f"{error_details} - {error_json}"
                except:
                    error_details = f"{error_details} - Response: {e.response.text[:200]}"
            
            return {
                "error": error_details,
                "content": None,
                "timestamp": datetime.now().isoformat()
            }
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """
        Simple generation interface.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            **kwargs: Additional parameters for chat()
            
        Returns:
            Generated text content
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = self.chat(messages, **kwargs)
        
        if response.get("error"):
            raise Exception(f"Groq API error: {response['error']}")
        
        return response["content"]
    
    def start_conversation(self, system_prompt: str):
        """Start a new conversation with system prompt."""
        self.conversation_history = [
            {"role": "system", "content": system_prompt}
        ]
    
    def add_message(self, role: str, content: str):
        """Add message to conversation history."""
        self.conversation_history.append({
            "role": role,
            "content": content
        })
    
    def get_response(self, user_message: str, **kwargs) -> str:
        """
        Get response in ongoing conversation.
        
        Args:
            user_message: User's message
            **kwargs: Additional parameters for chat()
            
        Returns:
            Assistant's response
        """
        self.add_message("user", user_message)
        
        response = self.chat(self.conversation_history, **kwargs)
        
        if response.get("error"):
            raise Exception(f"Groq API error: {response['error']}")
        
        assistant_message = response["content"]
        self.add_message("assistant", assistant_message)
        
        return assistant_message
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []
    
    def get_token_usage(self) -> Dict[str, int]:
        """Get approximate token usage (requires tracking in conversation)."""
        # This is approximate - actual usage returned in each API call
        total_chars = sum(len(msg["content"]) for msg in self.conversation_history)
        return {
            "estimated_tokens": total_chars // 4,  # Rough estimate
            "messages": len(self.conversation_history)
        }
