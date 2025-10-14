"""
Smart Model Selection Service

This service intelligently selects the best AI model based on:
- Task type (transcription, telegram history, general analysis)
- Context size (token estimation)
- Model capabilities and cost optimization
"""

import os
import logging
from typing import Dict, Any, Optional
from constants import (
    DEFAULT_OPENAI_MODEL, 
    DEFAULT_TRANSCRIPTION_MODEL, 
    GEMINI_MODEL,
    LARGE_CONTEXT_THRESHOLD,
    GEMINI_MAX_TOKENS
)

logger = logging.getLogger(__name__)

class SmartModelSelector:
    """Intelligent model selection based on task requirements and context size."""
    
    def __init__(self):
        self.google_api_key = os.getenv('GOOGLE_API_KEY')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        Rough estimation: ~4 characters per token for English text.
        """
        if not text:
            return 0
        
        # Simple estimation: ~4 characters per token
        # This is a rough estimate - for production, consider using tiktoken
        estimated_tokens = len(text) // 4
        return max(estimated_tokens, 1)
    
    def select_model(self, content: str, task_type: str, prompt: str = "") -> Dict[str, Any]:
        """
        Select the optimal model based on task type and context size.
        
        Args:
            content: The main content to analyze
            task_type: Type of task ('transcription', 'telegram_history', 'general_analysis')
            prompt: Additional prompt text
            
        Returns:
            Dict with model info: {
                'model_name': str,
                'provider': str,
                'api_key': str,
                'max_tokens': int,
                'reason': str
            }
        """
        
        # Calculate total context size (content + prompt)
        total_content = content + " " + prompt if prompt else content
        estimated_tokens = self.estimate_tokens(total_content)
        
        logger.info(f"Model selection: task_type={task_type}, estimated_tokens={estimated_tokens}")
        
        # Task-specific model selection
        if task_type == "transcription":
            return {
                'model_name': DEFAULT_TRANSCRIPTION_MODEL,
                'provider': 'openai',
                'api_key': self.openai_api_key,
                'max_tokens': 2000,
                'reason': 'Transcription task - using specialized transcription model'
            }
        
        elif task_type == "telegram_history":
            # Always use Gemini for Telegram histories (large context by nature)
            if not self.google_api_key:
                logger.warning("Google API key not found, falling back to GPT-5")
                return self._fallback_to_gpt5(estimated_tokens)
            
            return {
                'model_name': GEMINI_MODEL,
                'provider': 'google',
                'api_key': self.google_api_key,
                'max_tokens': GEMINI_MAX_TOKENS,
                'reason': 'Telegram history - always using Gemini for large context handling'
            }
        
        elif task_type == "general_analysis":
            # Smart selection based on context size
            if estimated_tokens >= LARGE_CONTEXT_THRESHOLD:
                # Large context - use Gemini
                if not self.google_api_key:
                    logger.warning("Google API key not found, falling back to GPT-5 with truncation")
                    return self._fallback_to_gpt5(estimated_tokens)
                
                return {
                    'model_name': GEMINI_MODEL,
                    'provider': 'google',
                    'api_key': self.google_api_key,
                    'max_tokens': GEMINI_MAX_TOKENS,
                    'reason': f'Large context ({estimated_tokens} tokens) - using Gemini for optimal performance'
                }
            else:
                # Small/medium context - use GPT-5
                return {
                    'model_name': DEFAULT_OPENAI_MODEL,
                    'provider': 'openai',
                    'api_key': self.openai_api_key,
                    'max_tokens': 2000,
                    'reason': f'Small context ({estimated_tokens} tokens) - using GPT-5 for efficiency'
                }
        
        else:
            # Unknown task type - default to GPT-5
            logger.warning(f"Unknown task type: {task_type}, defaulting to GPT-5")
            return {
                'model_name': DEFAULT_OPENAI_MODEL,
                'provider': 'openai',
                'api_key': self.openai_api_key,
                'max_tokens': 2000,
                'reason': f'Unknown task type - defaulting to GPT-5'
            }
    
    def _fallback_to_gpt5(self, estimated_tokens: int) -> Dict[str, Any]:
        """Fallback to GPT-5 when Gemini is unavailable."""
        return {
            'model_name': DEFAULT_OPENAI_MODEL,
            'provider': 'openai',
            'api_key': self.openai_api_key,
            'max_tokens': 2000,
            'reason': f'Fallback to GPT-5 (Gemini unavailable, {estimated_tokens} tokens)'
        }
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific model."""
        model_info = {
            'gpt-5': {
                'provider': 'openai',
                'max_context': 150000,
                'strengths': ['Reasoning', 'Code', 'General analysis'],
                'cost': 'high'
            },
            'gpt-4o-transcribe': {
                'provider': 'openai',
                'max_context': 128000,
                'strengths': ['Audio transcription', 'Speech recognition'],
                'cost': 'medium'
            },
            'gemini-2.0-flash-exp': {
                'provider': 'google',
                'max_context': 2000000,
                'strengths': ['Large context', 'Multimodal', 'Cost-effective'],
                'cost': 'low'
            }
        }
        
        return model_info.get(model_name, {
            'provider': 'unknown',
            'max_context': 0,
            'strengths': [],
            'cost': 'unknown'
        })

# Global instance
smart_selector = SmartModelSelector()

