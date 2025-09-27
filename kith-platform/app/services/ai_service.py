import os
import openai
from openai.error import OpenAIError
import google.generativeai as genai
from typing import Dict, Any, List
import logging
from app.utils.structured_logging import log_performance, StructuredLogger

logger = logging.getLogger(__name__)

class AIService:
    """
    A service class for interacting with the OpenAI API.
    It is instantiated by the dependency injection container.
    """
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        
        # Validate API keys - raise exceptions for invalid keys
        if not self.openai_api_key and not self.gemini_api_key:
            raise ValueError("No AI service configured - neither OPENAI_API_KEY nor GEMINI_API_KEY is set")
        
        # Check for obviously invalid keys
        if self.openai_api_key and self.openai_api_key == 'invalid_key':
            raise ValueError("Invalid OpenAI API key provided")
        if self.gemini_api_key and self.gemini_api_key == 'invalid_key':
            raise ValueError("Invalid Gemini API key provided")
            
        openai.api_key = self.openai_api_key

    @log_performance("ai_analysis")
    def analyze_note(self, content: str, contact_name: str) -> Dict[str, Any]:
        """Analyze a note and extract structured information"""
        try:
            # Use Gemini for analysis
            if self.gemini_api_key:
                return self._analyze_with_gemini(content, contact_name)
            elif self.openai_api_key:
                return self._analyze_with_openai(content, contact_name)
            else:
                raise ValueError("No AI service configured")
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            raise
    
    def _analyze_with_gemini(self, content: str, contact_name: str) -> Dict[str, Any]:
        """Analyze note using Google Gemini with retry logic for rate limits"""
        import time
        import json
        import re
        import google.api_core.exceptions
        
        model = genai.GenerativeModel('gemini-pro-latest')
        
        prompt = f"""
        Analyze this note about {contact_name} and extract structured information.
        Categorize the content into these categories: personal_info, preferences, relationships, work, interests, goals, concerns, other.
        
        Note content: {content}
        
        Return a JSON response with this structure:
        {{
            "categories": {{
                "personal_info": {{"content": "...", "confidence": 0.8}},
                "preferences": {{"content": "...", "confidence": 0.7}},
                "relationships": {{"content": "...", "confidence": 0.9}},
                "work": {{"content": "...", "confidence": 0.6}},
                "interests": {{"content": "...", "confidence": 0.7}},
                "goals": {{"content": "...", "confidence": 0.8}},
                "concerns": {{"content": "...", "confidence": 0.6}},
                "other": {{"content": "...", "confidence": 0.5}}
            }}
        }}
        
        Only include categories that have relevant content. Confidence should be between 0.0 and 1.0.
        """
        
        # Retry logic for rate limiting
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                response = model.generate_content(prompt)
                break
            except google.api_core.exceptions.ResourceExhausted as e:
                if "quota" in str(e).lower() or "429" in str(e):
                    if attempt < max_retries - 1:
                        logger.warning(f"Gemini API rate limit hit, retrying in {retry_delay}s (attempt {attempt + 1}/{max_retries})")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                        continue
                    else:
                        logger.error(f"Gemini API rate limit exceeded after {max_retries} attempts")
                        raise Exception(f"Gemini API rate limit exceeded: {e}")
                else:
                    raise
            except Exception as e:
                logger.error(f"Gemini API error: {e}")
                raise
        
        # Parse the JSON response - handle markdown code blocks
        response_text = response.text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith('```json'):
            response_text = response_text[7:]  # Remove ```json
        if response_text.startswith('```'):
            response_text = response_text[3:]   # Remove ```
        if response_text.endswith('```'):
            response_text = response_text[:-3]  # Remove trailing ```
        
        response_text = response_text.strip()
        
        return json.loads(response_text)
    
    def _analyze_with_openai(self, content: str, contact_name: str) -> Dict[str, Any]:
        """Analyze note using OpenAI GPT"""
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an AI assistant that analyzes personal notes and extracts structured information."},
                {"role": "user", "content": f"Analyze this note about {contact_name}: {content}"}
            ],
            temperature=0.3
        )
        
        # Parse the response and structure it
        # This is a simplified version - you'd want to implement proper parsing
        return {"categories": {"other": {"content": response.choices[0].message.content, "confidence": 0.8}}}
    
    def synthesize_note(self, content: str, contact_name: str) -> Dict[str, Any]:
        """Synthesize a note - alias for analyze_note for backward compatibility"""
        return self.analyze_note(content, contact_name)
