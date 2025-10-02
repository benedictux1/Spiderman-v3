import pytest
from unittest.mock import Mock, patch
from app.services.ai_service import AIService

@pytest.mark.unit
class TestAIService:
    
    def test_ai_service_initialization(self):
        """Test AI service initialization"""
        with patch('secure_credentials.load_openai_api_key', return_value=(None, None)), \
             patch('secure_credentials.SecureCredentialManager') as mock_manager, \
             patch.dict('os.environ', {'GEMINI_API_KEY': 'test_key', 'OPENAI_API_KEY': 'test_key'}):
            # Mock the SecureCredentialManager to return None for Gemini
            mock_manager.return_value.load_credentials.return_value = (None, None)
            service = AIService()
            assert service.gemini_api_key == 'test_key'
            assert service.openai_api_key == 'test_key'
    
    def test_ai_service_no_api_keys(self):
        """Test AI service initialization without API keys"""
        with patch('secure_credentials.load_openai_api_key', return_value=(None, None)), \
             patch('secure_credentials.SecureCredentialManager') as mock_manager, \
             patch.dict('os.environ', {}, clear=True):
            # Mock the SecureCredentialManager to return None for Gemini
            mock_manager.return_value.load_credentials.return_value = (None, None)
            service = AIService()
            assert service.gemini_api_key is None
            assert service.openai_api_key is None
            assert not service._available
    
    @patch('app.services.ai_service.genai')
    def test_analyze_note_with_gemini(self, mock_genai):
        """Test note analysis using Gemini"""
        # Setup mock
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = '{"categories": {"personal_info": {"content": "John is 30 years old", "confidence": 0.9}}}'
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        
        with patch('secure_credentials.load_openai_api_key', return_value=(None, None)), \
             patch('secure_credentials.SecureCredentialManager') as mock_manager, \
             patch.dict('os.environ', {'GEMINI_API_KEY': 'test_key'}):
            # Mock the SecureCredentialManager to return None for Gemini
            mock_manager.return_value.load_credentials.return_value = (None, None)
            service = AIService()
            result = service.analyze_note("John is 30 years old", "John Doe")
            
            assert 'categories' in result
            assert 'personal_info' in result['categories']
            assert result['categories']['personal_info']['content'] == "John is 30 years old"
            assert result['categories']['personal_info']['confidence'] == 0.9
    
    @patch('app.services.ai_service.openai')
    def test_analyze_note_with_openai(self, mock_openai):
        """Test note analysis using OpenAI"""
        # Setup mock
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "John is 30 years old"
        mock_openai.ChatCompletion.create.return_value = mock_response
        
        with patch('secure_credentials.load_openai_api_key', return_value=(None, None)), \
             patch('secure_credentials.SecureCredentialManager') as mock_manager, \
             patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}, clear=True):
            # Mock the SecureCredentialManager to return None for Gemini
            mock_manager.return_value.load_credentials.return_value = (None, None)
            service = AIService()
            result = service.analyze_note("John is 30 years old", "John Doe")
            
            assert 'categories' in result
            assert 'other' in result['categories']
            assert result['categories']['other']['confidence'] == 0.8
    
    def test_analyze_note_no_api_keys(self):
        """Test note analysis without any API keys - should use fallback analysis"""
        with patch('secure_credentials.load_openai_api_key', return_value=(None, None)), \
             patch('secure_credentials.SecureCredentialManager') as mock_manager, \
             patch.dict('os.environ', {}, clear=True):
            # Mock the SecureCredentialManager to return None for Gemini
            mock_manager.return_value.load_credentials.return_value = (None, None)
            service = AIService()
            
            # Should not raise exception, should use fallback analysis
            result = service.analyze_note("John works at Google", "John")
            assert 'categories' in result
            # Should have work category due to "works" keyword
            assert 'work' in result['categories']
    
    @patch('app.services.ai_service.genai')
    def test_analyze_note_gemini_failure(self, mock_genai):
        """Test note analysis when Gemini fails - should use fallback analysis"""
        mock_model = Mock()
        mock_model.generate_content.side_effect = Exception("API error")
        mock_genai.GenerativeModel.return_value = mock_model
        
        with patch('secure_credentials.load_openai_api_key', return_value=(None, None)), \
             patch('secure_credentials.SecureCredentialManager') as mock_manager, \
             patch.dict('os.environ', {'GEMINI_API_KEY': 'test_key'}):
            # Mock the SecureCredentialManager to return None for Gemini
            mock_manager.return_value.load_credentials.return_value = (None, None)
            service = AIService()
            
            # Should not raise exception, should use fallback analysis
            result = service.analyze_note("John works at Google", "John")
            assert 'categories' in result
            # Should have work category due to "works" keyword
            assert 'work' in result['categories']
    
    @patch('app.services.ai_service.genai')
    def test_analyze_note_invalid_json_response(self, mock_genai):
        """Test note analysis with invalid JSON response - should use fallback analysis"""
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = "Invalid JSON response"
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        
        with patch('secure_credentials.load_openai_api_key', return_value=(None, None)), \
             patch('secure_credentials.SecureCredentialManager') as mock_manager, \
             patch.dict('os.environ', {'GEMINI_API_KEY': 'test_key'}):
            # Mock the SecureCredentialManager to return None for Gemini
            mock_manager.return_value.load_credentials.return_value = (None, None)
            service = AIService()
            
            # Should not raise exception, should use fallback analysis
            result = service.analyze_note("John works at Google", "John")
            assert 'categories' in result
            # Should have work category due to "works" keyword
            assert 'work' in result['categories']
    
    def test_analyze_note_prefers_gemini_over_openai(self):
        """Test that Gemini is preferred over OpenAI when both are available"""
        with patch('secure_credentials.load_openai_api_key', return_value=(None, None)), \
             patch('secure_credentials.SecureCredentialManager') as mock_manager, \
             patch.dict('os.environ', {'GEMINI_API_KEY': 'test_key', 'OPENAI_API_KEY': 'test_key'}):
            # Mock the SecureCredentialManager to return None for Gemini
            mock_manager.return_value.load_credentials.return_value = (None, None)
            service = AIService()
            
            with patch('app.services.ai_service.genai') as mock_genai:
                mock_model = Mock()
                mock_response = Mock()
                mock_response.text = '{"categories": {"test": {"content": "test", "confidence": 0.8}}}'
                mock_model.generate_content.return_value = mock_response
                mock_genai.GenerativeModel.return_value = mock_model
                
                result = service.analyze_note("test content", "test contact")
                
                # Should use Gemini, not OpenAI
                mock_genai.GenerativeModel.assert_called_once()
                assert 'categories' in result