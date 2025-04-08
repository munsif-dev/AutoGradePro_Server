import json
import re
import stat
from rest_framework.response import Response
from django.shortcuts import render
from django.contrib.auth.models import User
from rest_framework import generics
from .serializers import AssignmentPageSerializer, FileListSerializer, LecturerSerializer, StudentSerializer, ModuleSerializer, AssignmentSerializer,  ScoreUpdateSerializer  , FileUploadSerializer, MarkingSchemeSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from .models import Lecturer, Student, Module, Assignment, Submission  , MarkingScheme, Answer, GradingResult
from rest_framework import status
import hashlib
from rest_framework.exceptions import NotFound
from django.db.models.functions import TruncMonth
from django.db.models import Count, Q
from django.http import JsonResponse
from rest_framework.filters import OrderingFilter, SearchFilter
from PyPDF2 import PdfReader
from docx import Document
import ollama 



def check_meaning_with_ollama(student_answer, correct_answer, question_text=None, threshold=0.7):
    """
    Uses Ollama to evaluate the semantic similarity between student and correct answers.
    
    Args:
        student_answer (str): The student's answer text
        correct_answer (str): The correct answer text
        question_text (str, optional): The question text to provide context
        threshold (float, optional): Confidence threshold for matching (0-1)
        
    Returns:
        tuple: (is_correct, confidence_score)
    """
    print(f"Student Answer: {student_answer}, Correct Answer: {correct_answer}")
    
    # Construct the prompt with question context if available
    system_prompt = "You are an AI assistant for grading papers. Your task is to compare student answers with correct answers." 
    
    if question_text:
        user_prompt = f"Question: {question_text}\n\nStudent Answer: {student_answer}\n\nCorrect Answer: {correct_answer}\n\nAre these answers semantically equivalent? Return a number from 0 to 1 representing the confidence score, where 1 means identical meaning and 0 means completely different meaning. Only return the number."
    else:
        user_prompt = f"Student Answer: {student_answer}\n\nCorrect Answer: {correct_answer}\n\nReturn a number from 0 to 1 representing how similar these answers are in meaning, where 1 means identical and 0 means completely different. Only return the number."
    
    try:
        response = ollama.chat(
            model="qwen2.5:1.5b",  
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
        )
        
        print(f"Ollama Response: {response}")
        content = response["message"]["content"].strip()
        
        # Try to extract just the number from the content
        try:
            # Look for a decimal number in the response
            match = re.search(r'\b([01](?:\.\d+)?|0\.\d+)\b', content)
            if match:
                confidence = float(match.group(1))
            else:
                # Fall back to simple true/false logic
                confidence = 1.0 if "true" in content.lower() else 0.0
                
            print(f"Confidence score: {confidence}")
            return (confidence >= threshold, confidence)
            
        except ValueError:
            # If we can't extract a number, fall back to simple true/false
            return ("true" in content.lower(), 0.5)
            
    except Exception as e:
        print(f"Error connecting to Ollama: {e}")
        return (False, 0.0)  # Return False with zero confidence



def get_or_create_grading_results(submission, marking_scheme):
    """
    Retrieves existing grading results or creates new ones if they don't exist.
    This function centralizes the grading logic to avoid duplication.
    Enhanced to use the improved grading capabilities.
    """
    # Check for existing grading results
    existing_results = GradingResult.objects.filter(submission=submission)
    
    if existing_results.exists():
        print(f"Using existing grading results for submission {submission.id}")
        # If results exist, return them and the calculated total score
        total_score = sum(result.marks_awarded for result in existing_results)
        return existing_results, total_score
    
    print(f"Creating new grading results for submission {submission.id}")
    # If no results exist, grade the submission and create results
    try:
        submission_answers = parse_submission_file(submission.file)
    except Exception as e:
        print(f"Error reading submission file: {e}")
        return [], 0

    total_score = 0
    grading_results = []

    for question_id, student_answer in submission_answers.items():
        if question_id in marking_scheme:
            scheme = marking_scheme[question_id]
            correct_answer = scheme["answer_text"]
            question_text = scheme.get("question_text", "")
            marks = scheme["marks"]
            
            # Get grading parameters from the scheme
            grading_type = scheme["grading_type"]
            case_sensitive = scheme["case_sensitive"]
            order_sensitive = scheme.get("order_sensitive", False)
            range_sensitive = scheme.get("range_sensitive", False)
            partial_matching = scheme.get("partial_matching", False)
            semantic_threshold = scheme.get("semantic_threshold", 0.7)
            answer_range = scheme.get("range", None)
            
            # Use the enhanced is_answer_correct function with all parameters
            grading_result = is_answer_correct(
                student_answer,
                correct_answer,
                grading_type,
                case_sensitive,
                order_sensitive,
                range_sensitive,
                answer_range,
                partial_matching,
                semantic_threshold,
                question_text
            )
            
            # Handle both boolean and dict return types
            if isinstance(grading_result, dict):
                is_correct = grading_result["is_correct"]
                score_percentage = grading_result["score_percentage"] / 100  # Convert to 0-1 scale
                explanation = grading_result["explanation"]
            else:
                # Boolean return type (backward compatibility)
                is_correct = grading_result
                score_percentage = 1.0 if is_correct else 0.0
                explanation = "Correct" if is_correct else "Incorrect"
            
            # Calculate marks based on score percentage for partial credit
            if partial_matching and grading_type == "list" and score_percentage > 0:
                # Give partial marks based on percentage correct
                marks_awarded = int(round(marks * score_percentage))
            else:
                # Traditional all-or-nothing grading
                marks_awarded = marks if is_correct else 0
                
            total_score += marks_awarded
            
            # Create a GradingResult object
            result = GradingResult(
                submission=submission,
                question_id=question_id,
                student_answer=student_answer,
                correct_answer=correct_answer,
                marks_awarded=marks_awarded,
                allocated_marks=marks,
                grading_type=grading_type,
                is_correct=is_correct
            )
            grading_results.append(result)
    
    # Bulk create all grading results if there are any
    if grading_results:
        GradingResult.objects.bulk_create(grading_results)
        
    # Return the newly created results and the total score
    return GradingResult.objects.filter(submission=submission), total_score


def get_markingScheme(assignment_id):
    """
    Retrieves the marking scheme for an assignment and formats it as a dictionary.
    Now includes question_text, partial_matching, and semantic_threshold.
    """
    try:
        marking_scheme = MarkingScheme.objects.get(assignment_id=assignment_id)
        answers = marking_scheme.answers.all()
        scheme_data = {
            idx + 1: {
                "question_text": answer.question_text or "",  # Include question text for context
                "answer_text": answer.answer_text.strip(),
                "marks": answer.marks,
                "grading_type": answer.grading_type,
                "case_sensitive": answer.case_sensitive,
                "order_sensitive": answer.order_sensitive,
                "range_sensitive": answer.range_sensitive,
                "partial_matching": answer.partial_matching,  # New field for partial matching
                "semantic_threshold": answer.semantic_threshold,  # New field for semantic threshold
                "range": answer.range,
            }
            for idx, answer in enumerate(answers)
        }
        return scheme_data
    except MarkingScheme.DoesNotExist:
        return None


def grade_submission(submission, marking_scheme):
    """
    Grades a submission and returns the total score.
    Uses existing results if available, otherwise creates new ones.
    """
    _, total_score = get_or_create_grading_results(submission, marking_scheme)
    
    # Update the submission score in the database
    if submission.score != total_score:
        submission.score = total_score
        submission.save(update_fields=['score'])
    
    return total_score

def get_answer_details(submission, marking_scheme):
    """
    Gets the detailed grading information for a submission.
    Uses existing results if available, otherwise creates new ones.
    """
    results, _ = get_or_create_grading_results(submission, marking_scheme)
    
    # Convert the results to the expected format
    answers_details = [
        {
            "question_id": result.question_id,
            "student_answer": result.student_answer,
            "correct_answer": result.correct_answer,
            "marks_for_answer": result.marks_awarded,
            "allocated_marks": result.allocated_marks,
        }
        for result in results
    ]
    
    return answers_details

def is_answer_correct(student_answer, correct_answer, grading_type, case_sensitive=False, 
                    order_sensitive=False, range_sensitive=False, answer_range=None, 
                    partial_matching=False, semantic_threshold=0.7, question_text=None):
    """
    Enhanced function to check if a student's answer is correct based on various grading types and parameters.
    
    Args:
        student_answer (str): The student's answer text
        correct_answer (str): The correct answer text
        grading_type (str): Type of grading to apply (one-word, short-phrase, list, numerical)
        case_sensitive (bool): Whether comparison should be case-sensitive
        order_sensitive (bool): Whether list items order matters
        range_sensitive (bool): Whether to use a range for numerical answers
        answer_range (dict): Range parameters for numerical answers
        partial_matching (bool): Allow partial credit for partially correct lists
        semantic_threshold (float): Confidence threshold for semantic matching
        question_text (str): The question text to provide context for semantic matching
        
    Returns:
        dict or bool: Result with grading details (if using new format) or boolean (if using old format)
    """
    # For backward compatibility, initialize result as a dict but may return boolean
    result = {
        "is_correct": False,
        "score_percentage": 0.0,
        "explanation": ""
    }
    
    # Handle empty answers
    if not student_answer or not correct_answer:
        result["explanation"] = "Missing student answer or correct answer"
        return False  # Maintaining backward compatibility

    # Normalize string inputs for consistent comparison
    # For numerical values, we'll convert later, but still need the string versions
    student_ans_str = str(student_answer).strip()
    correct_ans_str = str(correct_answer).strip()
    
    # Make answers case-insensitive if not case-sensitive
    student_ans = student_ans_str.lower() if not case_sensitive else student_ans_str
    correct_ans = correct_ans_str.lower() if not case_sensitive else correct_ans_str
    
    # ONE WORD grading - exact match with optional case sensitivity
    if grading_type == "one-word":
        student_clean = student_ans.strip()
        correct_clean = correct_ans.strip()
        
        is_correct = student_clean == correct_clean
        result["is_correct"] = is_correct
        result["score_percentage"] = 100.0 if is_correct else 0.0
        result["explanation"] = "Exact match" if is_correct else "Not an exact match"
        
        return is_correct  # For backward compatibility
        
    # SHORT PHRASE grading - semantic similarity using LLM with question context
    elif grading_type == "short-phrase":
        is_match, confidence = check_meaning_with_ollama(
            student_answer, correct_answer, question_text, semantic_threshold
        )
        
        result["is_correct"] = is_match
        result["score_percentage"] = confidence * 100
        result["explanation"] = f"Semantic similarity: {confidence:.2f}"
        
        return is_match  # For backward compatibility
        
    # LIST grading - compare lists with optional order sensitivity and partial matching
    elif grading_type == "list":
        # Normalize the student and correct answers with enhanced tokenization
        student_list = normalize_list_items(student_ans)
        correct_list = normalize_list_items(correct_ans)
        
        print(f"Normalized Student List: {student_list}, Normalized Correct List: {correct_list}")
        
        if order_sensitive:
            # When order matters, compare sequences directly
            if student_list == correct_list:
                result["is_correct"] = True
                result["score_percentage"] = 100.0
                result["explanation"] = "Perfect match with correct order"
                return True  # For backward compatibility
            elif partial_matching and len(student_list) > 0 and len(correct_list) > 0:
                # Calculate partial score for ordered lists using longest common subsequence
                lcs_length = longest_common_subsequence(student_list, correct_list)
                score = (lcs_length / len(correct_list)) * 100
                
                result["is_correct"] = score >= 100.0
                result["score_percentage"] = score
                result["explanation"] = f"Partial match with {score:.1f}% correctness (order matters)"
                return result["is_correct"]  # For backward compatibility
            else:
                result["explanation"] = "Lists don't match (order matters)"
                return False  # For backward compatibility
        else:
            # When order doesn't matter, compare as sets
            student_set = set(student_list)
            correct_set = set(correct_list)
            
            if student_set == correct_set:
                result["is_correct"] = True
                result["score_percentage"] = 100.0
                result["explanation"] = "Perfect match (all items present)"
                return True  # For backward compatibility
            elif partial_matching and len(student_set) > 0 and len(correct_set) > 0:
                # Calculate how many correct items the student has
                correct_items = student_set.intersection(correct_set)
                incorrect_items = student_set - correct_set
                missing_items = correct_set - student_set
                
                score = (len(correct_items) / len(correct_set)) * 100
                
                result["is_correct"] = score >= 100.0
                result["score_percentage"] = score
                result["explanation"] = f"Partial match: {len(correct_items)}/{len(correct_set)} items correct"
                
                return result["is_correct"]  # For backward compatibility
            else:
                result["explanation"] = "Lists don't match (order doesn't matter)"
                return False  # For backward compatibility
    
    # NUMERICAL grading - exact match or range with optional tolerance
    elif grading_type == "numerical":
        try:
            # Clean and convert to float for consistent numerical comparison
            # Handle commas, spaces, and other formatting issues
            student_numeric_str = student_ans_str.replace(',', '').replace(' ', '')
            correct_numeric_str = correct_ans_str.replace(',', '').replace(' ', '')
            
            # Convert to float for numerical comparison
            student_value = float(student_numeric_str)
            correct_value = float(correct_numeric_str)
            
            # For range-based checking
            if range_sensitive and answer_range:
                # Check if value is within the specified range
                min_val = float(answer_range.get("min", 0))
                max_val = float(answer_range.get("max", 0))
                tolerance_percent = float(answer_range.get("tolerance_percent", 0))
                
                # When range is specified, check if the value is within the range
                if min_val <= student_value <= max_val:
                    result["is_correct"] = True
                    result["score_percentage"] = 100.0
                    result["explanation"] = f"Value {student_value} is within acceptable range [{min_val}, {max_val}]"
                    return True  # For backward compatibility
                else:
                    # If tolerance is specified, check if value is within tolerance of either bound
                    if tolerance_percent > 0:
                        # Calculate tolerance amount based on closest bound
                        closest_bound = min_val if abs(student_value - min_val) < abs(student_value - max_val) else max_val
                        tolerance_amount = closest_bound * (tolerance_percent / 100)
                        
                        # Check if within tolerance
                        if student_value < min_val and student_value >= (min_val - tolerance_amount):
                            result["is_correct"] = True
                            result["score_percentage"] = 100.0
                            result["explanation"] = f"Value {student_value} is within tolerance of minimum {min_val}"
                            return True  # For backward compatibility
                        elif student_value > max_val and student_value <= (max_val + tolerance_amount):
                            result["is_correct"] = True
                            result["score_percentage"] = 100.0
                            result["explanation"] = f"Value {student_value} is within tolerance of maximum {max_val}"
                            return True  # For backward compatibility
                    
                    result["explanation"] = f"Value {student_value} is outside acceptable range [{min_val}, {max_val}]"
                    return False  # For backward compatibility
            else:
                # For exact numerical matching with small tolerance for floating point precision
                epsilon = 0.0001  # Small epsilon for floating point comparison
                
                if abs(student_value - correct_value) <= epsilon:
                    result["is_correct"] = True
                    result["score_percentage"] = 100.0
                    result["explanation"] = f"Exact numerical match: {student_value}"
                    return True  # For backward compatibility
                else:
                    # Calculate how close the student's answer is as a percentage
                    result["explanation"] = f"Numerical mismatch: expected {correct_value}, got {student_value}"
                    return False  # For backward compatibility
        except ValueError:
            result["explanation"] = f"Invalid numerical format: '{student_ans_str}' cannot be converted to a number"
            return False  # For backward compatibility
    else:
        result["explanation"] = f"Unknown grading type: {grading_type}"
        return False  # For backward compatibility



def normalize_list_items(answer):
    """
    Enhanced function to normalize a list answer string into individual items.
    Handles various delimiters and formats intelligently.
    """
    # First, detect if the answer uses bullet points, numbering, or other list formats
    if re.search(r'\n\s*[-•*]\s+', '\n' + answer) or re.search(r'\n\s*\d+\.\s+', '\n' + answer):
        # Split by line and extract content after bullet or number
        items = []
        for line in answer.split('\n'):
            # Match bullet points or numbered items
            match = re.match(r'\s*(?:[-•*]|\d+\.)\s+(.*)', line)
            if match and match.group(1).strip():
                items.append(match.group(1).strip())
        if items:
            return items
    
    # Otherwise, split on various delimiters
    items = re.split(r'[,;\t\n]+', answer)
    
    # Clean and normalize each item
    normalized_items = []
    for item in items:
        # Remove common list markers and extra whitespace
        clean_item = re.sub(r'^\s*[-•*]\s+|^\s*\d+\.\s+', '', item)
        clean_item = re.sub(r'\s+', ' ', clean_item).strip()
        
        if clean_item:
            normalized_items.append(clean_item)
    
    return normalized_items


def longest_common_subsequence(list1, list2):
    """
    Calculate the length of the longest common subsequence between two lists.
    Used for partial scoring of ordered lists.
    """
    m, n = len(list1), len(list2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if list1[i-1] == list2[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    
    return dp[m][n]

def parse_submission_file(file):
    answers = {}
    file_name = file.name.lower()

    if file_name.endswith(".txt"):
        answers = parse_txt_file(file)
    elif file_name.endswith(".pdf"):
        answers = parse_pdf_file(file)
    elif file_name.endswith(".docx"):
        answers = parse_docx_file(file)
    else:
        print(f"Unsupported file format: {file_name}")

 
    return answers

def parse_txt_file( file):
    file.open("r")
    lines = file.readlines()
    file.close()

    answers = {}
    pattern = r"^\s*(\d+)\s*[).:\-]?\s+(.*)$"

    for line in lines:
        line = line.strip()
        match = re.match(pattern, line)
        if match:
            question_no = int(match.group(1))
            answer_text = match.group(2).strip()
            answers[question_no] = normalize_answer(answer_text)
        else:
            print(f"Invalid line format: {line}")
    return answers

def parse_pdf_file( file):
    file.open("rb")
    reader = PdfReader(file)
    text = "".join(page.extract_text() for page in reader.pages)
    file.close()
    return extract_answers_from_text(text)

def parse_docx_file( file):
    file.open("rb")
    document = Document(file)
    text = "\n".join(para.text for para in document.paragraphs)
    file.close()
    return extract_answers_from_text(text)

def extract_answers_from_text(text):
    answers = {}
    lines = text.split("\n")
    pattern = r"^\s*(\d+)\s*[).:\-]?\s+(.*)$"

    for line in lines:
        line = line.strip()
        match = re.match(pattern, line)
        if match:
            question_no = int(match.group(1))
            answer_text = match.group(2).strip()
            answers[question_no] = normalize_answer(answer_text)
        else:
            print(f"Invalid line format: {line}")
    return answers

def normalize_answer( answer):
    # Normalize answer to remove extra spaces and handle mixed formats
    return re.sub(r"\s+", " ", answer.strip())



