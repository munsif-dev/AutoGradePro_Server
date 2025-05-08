from django.test import TestCase
from api.functions import (
    normalize_list_items, longest_common_subsequence,
    is_answer_correct, normalize_answer
)
import tempfile
import os
from django.core.files.uploadedfile import SimpleUploadedFile

class GradingFunctionsTest(TestCase):
    def test_normalize_list_items(self):
        """Test normalize_list_items function with various inputs"""
        # Test comma-separated list
        result = normalize_list_items("apple, banana, orange")
        self.assertEqual(result, ['apple', 'banana', 'orange'])
        
        # Test bulleted list
        result = normalize_list_items("- apple\n- banana\n- orange")
        self.assertEqual(result, ['apple', 'banana', 'orange'])
        
        # Test numbered list
        result = normalize_list_items("1. apple\n2. banana\n3. orange")
        self.assertEqual(result, ['apple', 'banana', 'orange'])
        
        # Test mixed format
        result = normalize_list_items("apple; banana, orange")
        self.assertEqual(result, ['apple', 'banana', 'orange'])

    def test_longest_common_subsequence(self):
        """Test longest_common_subsequence function"""
        # Test identical lists
        result = longest_common_subsequence(['a', 'b', 'c'], ['a', 'b', 'c'])
        self.assertEqual(result, 3)
        
        # Test partial match
        result = longest_common_subsequence(['a', 'b', 'c'], ['a', 'x', 'c'])
        self.assertEqual(result, 2)
        
        # Test no match
        result = longest_common_subsequence(['a', 'b', 'c'], ['x', 'y', 'z'])
        self.assertEqual(result, 0)
        
        # Test different lengths
        result = longest_common_subsequence(['a', 'b', 'c'], ['a', 'b', 'c', 'd'])
        self.assertEqual(result, 3)

    def test_normalize_answer(self):
        """Test normalize_answer function"""
        # Test with extra spaces
        result = normalize_answer("  test   answer  ")
        self.assertEqual(result, "test answer")
        
        # Test with newlines
        result = normalize_answer("test\nanswer")
        self.assertEqual(result, "test answer")

    def test_is_answer_correct_one_word(self):
        """Test is_answer_correct function with one-word grading type"""
        # Test exact match
        result = is_answer_correct("Paris", "Paris", "one-word", True)
        self.assertTrue(result)
        
        # Test case-insensitive match
        result = is_answer_correct("paris", "Paris", "one-word", False)
        self.assertTrue(result)
        
        # Test mismatch
        result = is_answer_correct("London", "Paris", "one-word", False)
        self.assertFalse(result)

    def test_is_answer_correct_list(self):
        """Test is_answer_correct function with list grading type"""
        # Test exact match with order sensitive
        result = is_answer_correct(
            "Red, Green, Blue", 
            "Red, Green, Blue", 
            "list", 
            False, 
            order_sensitive=True
        )
        self.assertTrue(result)
        
        # Test match with different order
        result = is_answer_correct(
            "Blue, Red, Green", 
            "Red, Green, Blue", 
            "list", 
            False, 
            order_sensitive=False
        )
        self.assertTrue(result)
        
        # Test partial match with partial matching enabled
        result = is_answer_correct(
            "Red, Green", 
            "Red, Green, Blue", 
            "list", 
            False, 
            order_sensitive=False,
            partial_matching=True
        )
        self.assertIsInstance(result, dict)
        self.assertFalse(result["is_correct"])
        self.assertGreater(result["score_percentage"], 0)
        
        # Test partial match with order sensitive
        result = is_answer_correct(
            "Red, Green", 
            "Red, Green, Blue", 
            "list", 
            False, 
            order_sensitive=True,
            partial_matching=True
        )
        self.assertIsInstance(result, dict)
        self.assertFalse(result["is_correct"])
        self.assertGreater(result["score_percentage"], 0)

    def test_is_answer_correct_numerical(self):
        """Test is_answer_correct function with numerical grading type"""
        # Test exact match
        result = is_answer_correct("42", "42", "numerical")
        self.assertTrue(result)
        
        # Test with different formats
        result = is_answer_correct("42.0", "42", "numerical")
        self.assertTrue(result)
        
        # Test with range
        result = is_answer_correct(
            "42", 
            "45", 
            "numerical", 
            range_sensitive=True,
            answer_range={"min": 40, "max": 50}
        )
        self.assertTrue(result)
        
        # Test outside range
        result = is_answer_correct(
            "35", 
            "45", 
            "numerical", 
            range_sensitive=True,
            answer_range={"min": 40, "max": 50}
        )
        self.assertFalse(result)
        
        # Test with tolerance
        result = is_answer_correct(
            "38", 
            "45", 
            "numerical", 
            range_sensitive=True,
            answer_range={"min": 40, "max": 50, "tolerance_percent": 10}
        )
        self.assertTrue(result)