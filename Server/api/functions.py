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



def check_meaning_with_ollama(student_answer, correct_answer):
    print(f"Student Answer: {student_answer}, Correct Answer: {correct_answer}")
  
    try:
        response = ollama.chat(
            model="qwen2.5:1.5b",  
            messages=[
                {"role": "system", "content": "You are an AI assistant for grading papers."},
                {"role": "user", "content": f"If these two answers are same, return true(only one word response), else return false: {student_answer} , {correct_answer}."},
            ],
            
            
        )
        print(f"Ollama Response: {response}")
        # Extract only the True/False response from the assistant's me
        answer = response["message"]["content"].strip().lower()

        # Return True if the answer is "true", else return False
        if "true" in answer:
            return True
        else:
            return False
    except Exception as e:
        print(f"Error connecting to Ollama: {e}")
        return False  # Return False or handle accordingly



def get_or_create_grading_results(submission, marking_scheme):
    """
    Retrieves existing grading results or creates new ones if they don't exist.
    This function centralizes the grading logic to avoid duplication.
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
            marks = scheme["marks"]
            
            # Check if the student's answer is correct
            is_correct = is_answer_correct(
                student_answer,
                correct_answer,
                scheme["grading_type"],
                scheme["case_sensitive"],
                scheme["order_sensitive"],
                scheme["range_sensitive"],
                scheme["range"],
            )
            
            marks_awarded = marks if is_correct else 0
            total_score += marks_awarded
            
            # Create a GradingResult object
            grading_result = GradingResult(
                submission=submission,
                question_id=question_id,
                student_answer=student_answer,
                correct_answer=correct_answer,
                marks_awarded=marks_awarded,
                allocated_marks=marks,
                grading_type=scheme["grading_type"],
                is_correct=is_correct
            )
            grading_results.append(grading_result)
    
    # Bulk create all grading results if there are any
    if grading_results:
        GradingResult.objects.bulk_create(grading_results)
        
    # Return the newly created results and the total score
    return GradingResult.objects.filter(submission=submission), total_score


def get_markingScheme(assignment_id):
    try:
        marking_scheme = MarkingScheme.objects.get(assignment_id=assignment_id)
        answers = marking_scheme.answers.all()
        scheme_data = {
            idx + 1: {
                "answer_text": answer.answer_text.strip(),
                "marks": answer.marks,
                "grading_type": answer.grading_type,
                "case_sensitive": answer.case_sensitive,
                "order_sensitive": answer.order_sensitive,
                "range_sensitive": answer.range_sensitive,
                "range": answer.range,
            }
            for idx, answer in enumerate(answers)
        }
        return scheme_data
    except MarkingScheme.DoesNotExist:
        return None

#def grade_submission( submission, marking_scheme):
    
    try:
        submission_answers = parse_submission_file(submission.file)
    except Exception as e:
        print(f"Error reading submission file: {e}")
        return 0

    total_score = 0

    for question_no, student_answer in submission_answers.items():
        if question_no in marking_scheme:
            scheme = marking_scheme[question_no]
            correct_answer = scheme["answer_text"]
            marks = scheme["marks"]

            if is_answer_correct(
                student_answer,
                correct_answer,
                scheme["grading_type"],
                scheme["case_sensitive"],
                scheme["order_sensitive"],
                scheme["range_sensitive"],
                scheme["range"],
            ):
                total_score += marks
    print(f"total score : {total_score}")

    return total_score

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

#def get_answer_details(submission, marking_scheme):
    try:
        # Parse the answers from the submission file
        submission_answers = parse_submission_file(submission.file)
    except Exception as e:
        print(f"Error reading submission file: {e}")
        return []

    answers_details = []

    for question_id, student_answer in submission_answers.items():
        if question_id in marking_scheme:
            scheme = marking_scheme[question_id]
            correct_answer = scheme["answer_text"]
            marks = scheme["marks"]
            
            # Check if the student's answer is correct
            marks_for_answer = 0
            if is_answer_correct(
                student_answer,
                correct_answer,
                scheme["grading_type"],
                scheme["case_sensitive"],
                scheme["order_sensitive"],
                scheme["range_sensitive"],
                scheme["range"],
            ):
                marks_for_answer = marks

            answers_details.append({
                "question_id": question_id,
                "student_answer": student_answer,
                "correct_answer": correct_answer,
                "marks_for_answer": marks_for_answer,
                "allocated_marks": marks,
            })

    return answers_details

def is_answer_correct(student_answer, correct_answer, grading_type, case_sensitive, order_sensitive, range_sensitive, answer_range):
    # Normalize case if case sensitivity is off
    if not case_sensitive:
        student_answer = student_answer.lower()
        correct_answer = correct_answer.lower()

    if grading_type == "short-phrase":
        return check_meaning_with_ollama(student_answer, correct_answer)
    elif grading_type == "one-word":
        return student_answer.strip() == correct_answer.strip()

    elif grading_type == "list":
        # Normalize the student and correct answers
        def normalize_list(answer, case_sensitive):
            # Split on various delimiters and remove descriptors like "- Order"
            items = re.split(r"[,\t\n;]+", answer)
            normalized_items = []
            for item in items:
                # Remove descriptors like "- Order" or "- Non Order"
                clean_item = re.sub(r"-\s*(order|non\s*order)", "", item, flags=re.IGNORECASE).strip()
                if clean_item:
                    normalized_items.append(clean_item.lower() if not case_sensitive else clean_item)
            return normalized_items

        student_list = normalize_list(student_answer, case_sensitive)
        correct_list = normalize_list(correct_answer, case_sensitive)

        print(f"Normalized Student List: {student_list}, Normalized Correct List: {correct_list}")

        if order_sensitive:
            # Compare the lists in their original order
            return student_list == correct_list
        else:
            # Compare the lists ignoring order
            return sorted(student_list) == sorted(correct_list)

    elif grading_type == "numerical":
      

        try:
            student_value = float(student_answer)
            

            if range_sensitive:
              
                return answer_range["min"] <= student_value <= answer_range["max"]
            else:
                return student_value == float(correct_answer)
                
        except ValueError:
            return False

    return False  # Default to incorrect for unhandled types

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

