from unittest import mock
from django.test import TestCase
from api.functions import check_meaning_with_ollama, parse_with_ollama

class OllamaIntegrationTest(TestCase):
    @mock.patch('api.functions.ollama.chat')
    def test_check_meaning_with_ollama(self, mock_chat):
        """Test check_meaning_with_ollama function with mocked Ollama response"""
        # Mock the Ollama response for a high confidence match
        mock_chat.return_value = {
            "message": {
                "content": "0.95"
            }
        }
        
        # Test with student and correct answers that are semantically similar
        is_correct, confidence = check_meaning_with_ollama(
            "The capital of France is Paris", 
            "Paris is the capital of France", 
            threshold=0.7
        )
        
        # Verify the result
        self.assertTrue(is_correct)
        self.assertEqual(confidence, 0.95)
        
        # Mock the Ollama response for a low confidence match
        mock_chat.return_value = {
            "message": {
                "content": "0.35"
            }
        }
        
        # Test with student and correct answers that are not semantically similar
        is_correct, confidence = check_meaning_with_ollama(
            "The capital of Italy is Rome", 
            "Paris is the capital of France", 
            threshold=0.7
        )
        
        # Verify the result
        self.assertFalse(is_correct)
        self.assertEqual(confidence, 0.35)
    
    @mock.patch('api.views.ollama.chat')
    def test_parse_with_ollama(self, mock_chat):
        """Test parse_with_ollama function with mocked Ollama response"""
        # This method is from ParseMarkingSchemeView
        from api.views import ParseMarkingSchemeView
        view = ParseMarkingSchemeView()
        
        # Mock the Ollama response for parsing content
        mock_chat.return_value = {
            "message": {
                "content": """
                [
                  {
                    "number": 1,
                    "question": "What is the capital of France?",
                    "answer": "Paris",
                    "marks": 5,
                    "gradingType": "one-word"
                  },
                  {
                    "number": 2,
                    "question": "List three primary colors",
                    "answer": "Red, Green, Blue",
                    "marks": 10,
                    "gradingType": "list"
                  }
                ]
                """
            }
        }
        
        # Test with sample content
        sample_content = "1. What is the capital of France? Paris (5 marks)\n2. List three primary colors: Red, Green, Blue (10 marks)"
        result = view.parse_with_ollama(sample_content)
        
        # Verify the result
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["number"], 1)
        self.assertEqual(result[0]["question"], "What is the capital of France?")
        self.assertEqual(result[0]["answer"], "Paris")
        self.assertEqual(result[0]["marks"], 5)
        self.assertEqual(result[0]["gradingType"], "one-word")
        
        self.assertEqual(result[1]["number"], 2)
        self.assertEqual(result[1]["question"], "List three primary colors")
        self.assertEqual(result[1]["answer"], "Red, Green, Blue")
        self.assertEqual(result[1]["marks"], 10)
        self.assertEqual(result[1]["gradingType"], "list")