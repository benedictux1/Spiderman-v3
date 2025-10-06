"""
Unified AI Service

Handles both OpenAI and Gemini AI models with smart selection.
"""

import os
import sys
import logging
import importlib.util
from typing import Dict, Any, Optional
from .smart_model_selector import smart_selector
from .gemini_service import gemini_service
from constants import DEFAULT_AI_TEMPERATURE

logger = logging.getLogger(__name__)

# Load _openai_chat from app.py at module level
try:
    spec = importlib.util.spec_from_file_location("app_main", 
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "app.py"))
    app_main = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app_main)
    _openai_chat = app_main._openai_chat
    logger.info("✅ Successfully loaded _openai_chat from app.py")
except Exception as e:
    logger.error(f"❌ Failed to load _openai_chat: {e}")
    _openai_chat = None

class UnifiedAIService:
    """Unified service for AI analysis using smart model selection."""
    
    def __init__(self):
        self.smart_selector = smart_selector
        self.gemini_service = gemini_service
        
    def analyze_content(self, content: str, task_type: str, prompt: str = "") -> Dict[str, Any]:
        """
        Analyze content using the optimal AI model.
        
        Args:
            content: The content to analyze
            task_type: Type of task ('transcription', 'telegram_history', 'general_analysis')
            prompt: Additional prompt/instruction
            
        Returns:
            Dict with analysis results
        """
        try:
            # Select the optimal model
            model_info = self.smart_selector.select_model(content, task_type, prompt)
            logger.info(f"Selected model: {model_info['model_name']} ({model_info['reason']})")
            
            # Prepare the full prompt
            full_prompt = f"{prompt}\n\nContent to analyze:\n{content}" if prompt else content
            
            # Route to appropriate service
            if model_info['provider'] == 'google':
                return self._analyze_with_gemini(full_prompt, model_info)
            elif model_info['provider'] == 'openai':
                return self._analyze_with_openai(full_prompt, model_info)
            else:
                raise ValueError(f"Unknown provider: {model_info['provider']}")
                
        except Exception as e:
            logger.error(f"AI analysis failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'model': 'unknown',
                'provider': 'unknown',
                'reason': f'Analysis failed: {str(e)}'
            }
    
    def _analyze_with_gemini(self, prompt: str, model_info: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze content using Gemini."""
        try:
            if not self.gemini_service:
                raise ValueError("Gemini service not available")
            
            result = self.gemini_service.analyze_content(
                prompt, 
                max_tokens=model_info['max_tokens']
            )
            
            if result['success']:
                logger.info(f"Gemini analysis successful: {result['reason']}")
                return result
            else:
                raise Exception(result['error'])
                
        except Exception as e:
            logger.error(f"Gemini analysis failed: {str(e)}")
            # Fallback to OpenAI if Gemini fails
            logger.info("Falling back to OpenAI due to Gemini failure")
            return self._fallback_to_openai(prompt, model_info)
    
    def _analyze_with_openai(self, prompt: str, model_info: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze content using OpenAI."""
        try:
            if _openai_chat is None:
                raise Exception("OpenAI chat function not available")
            
            response_content = _openai_chat(
                messages=[{"role": "user", "content": prompt}],
                model=model_info['model_name'],
                max_tokens=model_info['max_tokens'],
                temperature=DEFAULT_AI_TEMPERATURE,
            )
            
            return {
                'success': True,
                'content': response_content,
                'model': model_info['model_name'],
                'provider': 'openai',
                'reason': f'OpenAI analysis completed with {model_info["model_name"]}'
            }
            
        except Exception as e:
            logger.error(f"OpenAI analysis failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'model': model_info['model_name'],
                'provider': 'openai',
                'reason': f'OpenAI analysis failed: {str(e)}'
            }
    
    def _fallback_to_openai(self, prompt: str, model_info: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback to OpenAI when Gemini fails."""
        try:
            if _openai_chat is None:
                raise Exception("OpenAI chat function not available")
            
            # Use GPT-5 as fallback
            response_content = _openai_chat(
                messages=[{"role": "user", "content": prompt}],
                model='gpt-5',
                max_tokens=2000,
                temperature=DEFAULT_AI_TEMPERATURE,
            )
            
            return {
                'success': True,
                'content': response_content,
                'model': 'gpt-5',
                'provider': 'openai',
                'reason': 'Fallback to GPT-5 due to Gemini failure'
            }
            
        except Exception as e:
            logger.error(f"Fallback OpenAI analysis failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'model': 'gpt-5',
                'provider': 'openai',
                'reason': f'Fallback analysis failed: {str(e)}'
            }
    
    def get_available_models(self) -> Dict[str, Any]:
        """Get information about available models."""
        return {
            'openai': {
                'gpt-5': self.smart_selector.get_model_info('gpt-5'),
                'gpt-4o-transcribe': self.smart_selector.get_model_info('gpt-4o-transcribe')
            },
            'google': {
                'gemini-2.0-flash-exp': self.smart_selector.get_model_info('gemini-2.0-flash-exp')
            },
            'smart_selector': {
                'threshold': '150K tokens',
                'telegram_history': 'Always Gemini',
                'transcription': 'Always GPT-4o Transcribe',
                'general_analysis': 'GPT-5 < 150K tokens, Gemini ≥ 150K tokens'
            }
        }

# Global instance
unified_ai_service = UnifiedAIService()

