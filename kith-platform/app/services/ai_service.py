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
        # Initialize with None values
        self.openai_api_key = None
        self.gemini_api_key = None
        
        # Try to load from secure credentials first
        try:
            from secure_credentials import load_openai_api_key
            secure_openai_key, model = load_openai_api_key()
            if secure_openai_key:
                self.openai_api_key = secure_openai_key
                logger.info("Loaded OpenAI API key from secure storage")
        except Exception as e:
            logger.warning(f"Could not load OpenAI key from secure storage: {e}")
        
        # Try to load Gemini key from secure storage
        try:
            from secure_credentials import SecureCredentialManager
            manager = SecureCredentialManager('.gemini_credentials.enc')
            secure_gemini_key, model = manager.load_credentials()
            if secure_gemini_key:
                self.gemini_api_key = secure_gemini_key
                logger.info("Loaded Gemini API key from secure storage")
        except Exception as e:
            logger.warning(f"Could not load Gemini key from secure storage: {e}")
        
        # If no secure keys, fall back to environment variables
        if not self.openai_api_key:
            self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.gemini_api_key:
            self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        
        # Validate API keys - be more lenient for testing
        if not self.openai_api_key and not self.gemini_api_key:
            logger.warning("No AI service configured - neither OPENAI_API_KEY nor GEMINI_API_KEY is set")
            # Don't raise exception, allow service to be created but mark as unavailable
            self._available = False
        else:
            self._available = True
            
        # Check for obviously invalid keys
        if self.openai_api_key and self.openai_api_key == 'invalid_key':
            logger.warning("Invalid OpenAI API key provided")
            self.openai_api_key = None
        if self.gemini_api_key and self.gemini_api_key == 'invalid_key':
            logger.warning("Invalid Gemini API key provided")
            self.gemini_api_key = None
            
        if self.openai_api_key:
            openai.api_key = self.openai_api_key

    @log_performance("ai_analysis")
    def analyze_note(self, content: str, contact_name: str) -> Dict[str, Any]:
        """Analyze a note and extract structured information"""
        try:
            # Check if service is available
            if not self._available:
                logger.warning("AI service not available - returning fallback analysis")
                return self._fallback_analysis(content, contact_name)
            
            # Use Gemini for analysis (preferred)
            if self.gemini_api_key:
                try:
                    return self._analyze_with_gemini(content, contact_name)
                except Exception as e:
                    logger.warning(f"Gemini analysis failed: {e}")
                    if self.openai_api_key:
                        logger.info("Falling back to OpenAI")
                        return self._analyze_with_openai(content, contact_name)
                    else:
                        return self._fallback_analysis(content, contact_name)
            elif self.openai_api_key:
                try:
                    return self._analyze_with_openai(content, contact_name)
                except Exception as e:
                    logger.warning(f"OpenAI analysis failed: {e}")
                    return self._fallback_analysis(content, contact_name)
            else:
                logger.warning("No AI service configured - using fallback analysis")
                return self._fallback_analysis(content, contact_name)
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return self._fallback_analysis(content, contact_name)
    
    def _analyze_with_gemini(self, content: str, contact_name: str) -> Dict[str, Any]:
        """Analyze note using Google Gemini with retry logic for rate limits"""
        import time
        import json
        import re
        import google.api_core.exceptions
        
        model = genai.GenerativeModel('gemini-pro-latest')
        
        prompt = f"""
        Analyze this note about {contact_name} and extract structured information.
        
        Categorize the content into these categories (only include if relevant):
        
        CATEGORY_DEFINITIONS:
        - Actionable: Immediate tasks, follow-ups, reminders, requests, or discussion topics requiring attention within days or weeks.
        - Goals: Clearly defined aspirations and objectives across all life domains, including short-term targets (3-12 months), medium-term goals (1-5 years), and long-term visions (5+ years).
        - Relationship_Strategy: Structured approaches to nurturing, deepening, or improving your relationship with specific tactics for connection and support.
        - Social: Comprehensive mapping of their social ecosystem including family dynamics, friendship networks, romantic relationships, professional connections, community involvement.
        - Professional_Background: Detailed career history and occupational profile including employment timeline, educational credentials, skill inventory, achievement record.
        - Financial_Situation: Comprehensive portrait of their economic circumstances, money management approach, and financial outlook.
        - Wellbeing: Holistic health status encompassing physical, mental, emotional, and spiritual dimensions.
        - Avocation: Comprehensive inventory of non-professional interests, passions, and recreational activities.
        - Environment_And_Lifestyle: Detailed portrait of their daily living context and routine patterns.
        - Psychology_And_Values: In-depth profile of their mental frameworks, belief systems, and guiding principles.
        - Communication_Style: Comprehensive analysis of their interpersonal communication patterns and preferences across all contexts.
        - Challenges_And_Development: Nuanced exploration of their struggles, growth areas, and evolution across personal and professional domains.
        - Deeper_Insights: Profound observations about their core essence, philosophical outlook, and unique qualities that transcend conventional categorization.
        - Admin_matters: Administrative details including important dates, birthdays, anniversaries, and other key information to track.
        - Others: Any other important information that doesn't fit into the categories above.
        
        Note content: {content}
        
        Return a JSON response with this structure:
        {{
            "categories": {{
                "Actionable": {{"content": "specific factual information extracted", "confidence": 0.85}},
                "Goals": {{"content": "specific factual information extracted", "confidence": 0.80}},
                "Social": {{"content": "specific factual information extracted", "confidence": 0.90}}
            }}
        }}
        
        IMPORTANT:
        - Only include categories that have relevant content from the note
        - Extract specific, factual information - not interpretations
        - Confidence should be between 0.0 and 1.0 based on clarity of information
        - Be precise and concise in your extraction
        - Focus on actionable insights and meaningful categorization
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
        import json
        
        system_prompt = """You are an AI assistant that analyzes personal notes and extracts structured information into specific categories.

Available categories:
- Actionable: Immediate tasks, follow-ups, reminders, requests requiring attention
- Goals: Aspirations and objectives across all life domains (short/medium/long-term)
- Relationship_Strategy: Structured approaches to nurturing relationships
- Social: Social ecosystem including family, friends, romantic, professional connections
- Professional_Background: Career history, credentials, skills, achievements
- Financial_Situation: Economic circumstances, money management, financial outlook
- Wellbeing: Holistic health status (physical, mental, emotional, spiritual)
- Avocation: Non-professional interests, passions, recreational activities
- Environment_And_Lifestyle: Daily living context and routine patterns
- Psychology_And_Values: Mental frameworks, belief systems, guiding principles
- Communication_Style: Interpersonal communication patterns and preferences
- Challenges_And_Development: Struggles, growth areas, evolution
- Deeper_Insights: Core essence, philosophical outlook, unique qualities
- Admin_matters: Important dates, birthdays, anniversaries, key information
- Others: Information that doesn't fit other categories

Return ONLY a JSON object with this structure:
{
    "categories": {
        "category_name": {"content": "specific factual information", "confidence": 0.85}
    }
}

Only include categories with relevant content. Be factual and precise."""

        user_prompt = f"""Analyze this note about {contact_name} and extract structured information:

{content}

Return ONLY the JSON response."""

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3
        )
        
        # Parse the JSON response
        try:
            result = json.loads(response.choices[0].message.content)
            return result
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return {"categories": {"other": {"content": response.choices[0].message.content, "confidence": 0.6}}}
    
    def _fallback_analysis(self, content: str, contact_name: str) -> Dict[str, Any]:
        """Fallback analysis when AI services are unavailable"""
        logger.info("Using fallback analysis - AI services unavailable")
        
        # Simple keyword-based analysis as fallback
        content_lower = content.lower()
        
        # Basic categorization based on keywords
        categories = {}
        
        # Personal info keywords
        personal_keywords = ['age', 'birthday', 'born', 'phone', 'email', 'address', 'lives in', 'from']
        if any(keyword in content_lower for keyword in personal_keywords):
            categories['personal_info'] = {
                'content': content,
                'confidence': 0.6
            }
        
        # Work keywords
        work_keywords = ['work', 'job', 'company', 'office', 'career', 'profession', 'boss', 'colleague']
        if any(keyword in content_lower for keyword in work_keywords):
            categories['work'] = {
                'content': content,
                'confidence': 0.7
            }
        
        # Relationship keywords
        relationship_keywords = ['family', 'friend', 'spouse', 'partner', 'relationship', 'married', 'single']
        if any(keyword in content_lower for keyword in relationship_keywords):
            categories['relationships'] = {
                'content': content,
                'confidence': 0.8
            }
        
        # If no specific categories found, put in 'other'
        if not categories:
            categories['other'] = {
                'content': content,
                'confidence': 0.5
            }
        
        return {'categories': categories}
    
    def synthesize_note(self, content: str, contact_name: str) -> Dict[str, Any]:
        """Synthesize a note - alias for analyze_note for backward compatibility"""
        return self.analyze_note(content, contact_name)
