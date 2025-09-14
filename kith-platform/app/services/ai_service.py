import os
import openai
import google.generativeai as genai
from typing import Dict, Any, List
import logging
from app.utils.structured_logging import log_performance, StructuredLogger

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        
        # Initialize OpenAI
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
        
        # Initialize Gemini
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
    
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
        """Analyze note using Google Gemini"""
        model = genai.GenerativeModel('gemini-pro')
        
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
        
        response = model.generate_content(prompt)
        # Parse the JSON response
        import json
        return json.loads(response.text)
    
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
