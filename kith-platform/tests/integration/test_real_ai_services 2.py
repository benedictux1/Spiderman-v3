import pytest
import os
import time
import google.api_core.exceptions
from app.services.ai_service import AIService

@pytest.mark.integration
@pytest.mark.slow
class TestRealAIServices:
    """Real AI service tests (not mocked) - these take 2-5 seconds each"""
    
    def test_gemini_api_connectivity(self):
        """Test if Gemini Pro is actually reachable"""
        if not os.getenv('GEMINI_API_KEY'):
            pytest.skip("GEMINI_API_KEY not set - skipping real AI test")
        
        ai_service = AIService()
        
        # Simple test to see if API responds
        result = ai_service.analyze_note(
            content="Test note for connectivity check",
            contact_name="Test Contact"
        )
        
        assert result is not None
        assert 'categories' in result
        print(f"✅ Gemini Pro is working: {result}")
    
    def test_openai_api_connectivity(self):
        """Test if OpenAI API is actually reachable"""
        if not os.getenv('OPENAI_API_KEY'):
            pytest.skip("OPENAI_API_KEY not set - skipping real AI test")
        
        # Temporarily disable Gemini to force OpenAI usage
        original_gemini_key = os.getenv('GEMINI_API_KEY')
        os.environ['GEMINI_API_KEY'] = ''
        
        try:
            ai_service = AIService()
            
            result = ai_service.analyze_note(
                content="Test note for OpenAI connectivity check",
                contact_name="Test Contact"
            )
            
            assert result is not None
            assert 'categories' in result
            print(f"✅ OpenAI API is working: {result}")
        finally:
            # Restore original Gemini key
            if original_gemini_key:
                os.environ['GEMINI_API_KEY'] = original_gemini_key
            else:
                os.environ.pop('GEMINI_API_KEY', None)
    
    def test_ai_analysis_quality_gemini(self):
        """Test if Gemini is producing meaningful results"""
        if not os.getenv('GEMINI_API_KEY'):
            pytest.skip("GEMINI_API_KEY not set - skipping real AI test")
        
        ai_service = AIService()
        
        result = ai_service.analyze_note(
            content="Had lunch with Sarah yesterday. She mentioned her new job at Google and is excited about the new role.",
            contact_name="Sarah"
        )
        
        # Check if AI actually analyzed the content
        assert 'categories' in result
        assert len(str(result)) > 50  # Should be substantial
        
        # Check if key information was captured
        result_str = str(result).lower()
        assert 'job' in result_str or 'google' in result_str or 'lunch' in result_str
        print(f"✅ Gemini analysis quality: {result}")
    
    def test_ai_analysis_quality_openai(self):
        """Test if OpenAI is producing meaningful results"""
        if not os.getenv('OPENAI_API_KEY'):
            pytest.skip("OPENAI_API_KEY not set - skipping real AI test")
        
        # Temporarily disable Gemini to force OpenAI usage
        original_gemini_key = os.getenv('GEMINI_API_KEY')
        os.environ['GEMINI_API_KEY'] = ''
        
        try:
            ai_service = AIService()
            
            result = ai_service.analyze_note(
                content="Meeting with John about the project deadline. He's concerned about the timeline.",
                contact_name="John"
            )
            
            # Check if AI actually analyzed the content
            assert 'categories' in result
            assert len(str(result)) > 20  # Should be substantial
            
            # Check if key information was captured
            result_str = str(result).lower()
            assert 'project' in result_str or 'deadline' in result_str or 'meeting' in result_str
            print(f"✅ OpenAI analysis quality: {result}")
        finally:
            # Restore original Gemini key
            if original_gemini_key:
                os.environ['GEMINI_API_KEY'] = original_gemini_key
            else:
                os.environ.pop('GEMINI_API_KEY', None)
    
    def test_ai_service_error_handling(self):
        """Test what happens when AI service fails"""
        # Test with invalid API key
        original_gemini_key = os.getenv('GEMINI_API_KEY')
        original_openai_key = os.getenv('OPENAI_API_KEY')
        
        try:
            os.environ['GEMINI_API_KEY'] = 'invalid_key'
            os.environ['OPENAI_API_KEY'] = 'invalid_key'
            
            # Test that the service raises an exception when trying to initialize
            # This should fail because the API keys are invalid
            with pytest.raises(ValueError, match="Invalid.*API key"):
                AIService()
        finally:
            # Restore original keys
            if original_gemini_key:
                os.environ['GEMINI_API_KEY'] = original_gemini_key
            else:
                os.environ.pop('GEMINI_API_KEY', None)
            
            if original_openai_key:
                os.environ['OPENAI_API_KEY'] = original_openai_key
            else:
                os.environ.pop('OPENAI_API_KEY', None)
    
    def test_ai_service_fallback(self):
        """Test if system falls back to OpenAI when Gemini fails"""
        if not os.getenv('OPENAI_API_KEY'):
            pytest.skip("OPENAI_API_KEY not set - skipping fallback test")
        
        # Disable Gemini to test fallback
        original_gemini_key = os.getenv('GEMINI_API_KEY')
        os.environ['GEMINI_API_KEY'] = ''
        
        try:
            ai_service = AIService()
            
            result = ai_service.analyze_note(
                content="Test fallback functionality",
                contact_name="Test Contact"
            )
            
            assert result is not None
            assert 'categories' in result
            print(f"✅ Fallback to OpenAI working: {result}")
        finally:
            # Restore original Gemini key
            if original_gemini_key:
                os.environ['GEMINI_API_KEY'] = original_gemini_key
            else:
                os.environ.pop('GEMINI_API_KEY', None)
    
    def test_ai_response_time(self):
        """Test AI service response times"""
        if not os.getenv('GEMINI_API_KEY') and not os.getenv('OPENAI_API_KEY'):
            pytest.skip("No AI API keys set - skipping response time test")
        
        ai_service = AIService()
        
        start_time = time.time()
        result = ai_service.analyze_note(
            content="Quick response time test",
            contact_name="Test Contact"
        )
        duration = time.time() - start_time
        
        assert result is not None
        assert duration < 10.0  # Should complete within 10 seconds
        print(f"✅ AI response time: {duration:.2f} seconds")
    
    def test_ai_service_with_complex_content(self):
        """Test AI service with complex, realistic content"""
        if not os.getenv('GEMINI_API_KEY') and not os.getenv('OPENAI_API_KEY'):
            pytest.skip("No AI API keys set - skipping complex content test")
        
        ai_service = AIService()
        
        complex_content = """
        Had a great meeting with Dr. Sarah Johnson yesterday at the coffee shop downtown. 
        She mentioned she's starting a new research project on machine learning applications 
        in healthcare. She's really excited about the potential impact on patient care. 
        We discussed collaborating on a paper about AI ethics in medical diagnosis. 
        She's planning to present her findings at the upcoming AI conference in San Francisco. 
        She also mentioned her concerns about data privacy in healthcare AI systems.
        """
        
        result = ai_service.analyze_note(
            content=complex_content,
            contact_name="Dr. Sarah Johnson"
        )
        
        assert result is not None
        assert 'categories' in result
        
        # Check if multiple categories were identified
        categories = result.get('categories', {})
        assert len(categories) > 0
        
        # Check if key information was captured
        result_str = str(result).lower()
        assert any(keyword in result_str for keyword in ['research', 'healthcare', 'ai', 'conference'])
        print(f"✅ Complex content analysis: {len(categories)} categories identified")
