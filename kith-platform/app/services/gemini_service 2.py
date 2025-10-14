"""
Gemini AI Service

Handles Google Gemini API integration for large context analysis.
"""

import os
import logging
import google.generativeai as genai
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class GeminiService:
    """Service for interacting with Google Gemini AI models."""
    
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_API_KEY')
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        logger.info("Gemini service initialized successfully")
    
    def analyze_content(self, prompt: str, max_tokens: int = 1000000) -> Dict[str, Any]:
        """
        Analyze content using Gemini model.
        
        Args:
            prompt: The prompt/instruction for analysis
            max_tokens: Maximum tokens for response
            
        Returns:
            Dict with analysis results
        """
        try:
            logger.info(f"Analyzing content with Gemini (max_tokens: {max_tokens})")
            
            # Generate content using Gemini
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=0.1,
                    top_p=0.8,
                    top_k=40
                )
            )
            
            if not response.text:
                raise ValueError("Empty response from Gemini")
            
            logger.info(f"Gemini analysis completed successfully")
            
            return {
                'success': True,
                'content': response.text,
                'model': 'gemini-2.0-flash-exp',
                'provider': 'google',
                'tokens_used': len(response.text.split()) * 1.3,  # Rough estimate
                'reason': 'Gemini analysis completed'
            }
            
        except Exception as e:
            logger.error(f"Gemini analysis failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'model': 'gemini-2.0-flash-exp',
                'provider': 'google',
                'reason': f'Gemini analysis failed: {str(e)}'
            }
    
    def is_available(self) -> bool:
        """Check if Gemini service is available."""
        try:
            # Simple test to check if API key works
            test_response = self.model.generate_content("Hello")
            return test_response.text is not None
        except Exception as e:
            logger.warning(f"Gemini availability check failed: {str(e)}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the Gemini model."""
        return {
            'model_name': 'gemini-2.0-flash-exp',
            'provider': 'google',
            'max_context': 2000000,
            'max_output_tokens': 1000000,
            'strengths': [
                'Large context handling',
                'Multimodal capabilities',
                'Cost-effective for large contexts',
                'Fast processing'
            ],
            'limitations': [
                'Newer model (less battle-tested)',
                'Different response format than OpenAI'
            ]
        }

# Global instance
try:
    gemini_service = GeminiService()
    logger.info("Gemini service initialized successfully")
except Exception as e:
    logger.warning(f"Failed to initialize Gemini service: {str(e)}")
    gemini_service = None

