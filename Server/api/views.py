import json
import os
import re
import stat
from rest_framework.response import Response
from django.shortcuts import render
from django.contrib.auth.models import User
from rest_framework import generics
from .serializers import AssignmentPageSerializer, FileListSerializer, LecturerSerializer, UserSerializer, StudentSerializer, ModuleSerializer, AssignmentSerializer,  ScoreUpdateSerializer  , FileUploadSerializer, MarkingSchemeSerializer, GradingResultSerializer
from .serializers import LecturerProfileSerializer, PasswordChangeSerializer, UserProfileSerializer
from .serializers import LecturerDetailSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.views import APIView
from .models import Lecturer, Student, Module, Assignment, Submission  , MarkingScheme, Answer, GradingResult
from rest_framework import status
import hashlib
import numpy as np
from rest_framework.exceptions import NotFound
from django.db.models.functions import TruncMonth, TruncWeek, TruncDay
from django.db.models import Count, Q
from django.http import JsonResponse
from rest_framework.filters import OrderingFilter, SearchFilter
from .functions  import  get_markingScheme,get_answer_details, grade_submission, parse_submission_file, is_answer_correct, parse_txt_file, parse_pdf_file, parse_docx_file, extract_answers_from_text, normalize_answer
import logging
import tempfile
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q
import ollama

logger = logging.getLogger(__name__)


class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        stats = {
            "modules_created": Module.objects.filter(lecturer__user=user).count(),
            "assignments_created": Assignment.objects.filter(module__lecturer__user=user).count(),
            "files_uploaded": Submission.objects.filter(assignment__module__lecturer__user=user).count(),
            "submissions_received": MarkingScheme.objects.filter(assignment__module__lecturer__user=user).distinct().count(),
        }
        return Response(stats)


class ModuleListCreate(generics.ListCreateAPIView):
    serializer_class = ModuleSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Only allow the lecturer who owns the module to delete it
        user = self.request.user
        if hasattr(user, 'lecturer'):  # Check if the user is a lecturer
            return Module.objects.filter(lecturer=user.lecturer)
        return Module.objects.none()  # Prevent unauthorized users
    
    
    def perform_create(self, serializer):
        user = self.request.user
        try:
            # Get the associated lecturer
            lecturer = Lecturer.objects.get(user=user)
            # Save the new module with the lecturer
            serializer.save(lecturer=lecturer)
        except Lecturer.DoesNotExist:
            # Raise an error or handle appropriately if no lecturer is found
            raise Exception("The user is not associated with a lecturer.")
        
class ModuleListView(generics.ListAPIView):
    """
    API view to fetch all modules associated with the authenticated lecturer.
    """
    serializer_class = ModuleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'lecturer'):  # Check if the user is a lecturer
            return Module.objects.filter(lecturer=user.lecturer)
        return Module.objects.none()  # Return empty queryset if not a lecturer
    
class ModuleDetailView(generics.RetrieveAPIView):
    """
    API view to fetch a specific module.
    Only the lecturer who owns the module can access this view.
    """
    serializer_class = ModuleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'lecturer'):  # Check if the user is a lecturer
            return Module.objects.filter(lecturer=user.lecturer)
        return Module.objects.none()  # Prevent unauthorized users
    
class ModuleDeleteView(generics.DestroyAPIView):
    serializer_class = ModuleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Only allow the lecturer who owns the module to delete it
        user = self.request.user
        if hasattr(user, 'lecturer'):  # Check if the user is a lecturer
            return Module.objects.filter(lecturer=user.lecturer)
        return Module.objects.none()  # Prevent unauthorized users
    
class ModuleUpdateView(generics.UpdateAPIView):
    """
    API view to update a specific module's details.
    Only the lecturer who owns the module can access this view.
    """
    serializer_class = ModuleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'lecturer'):  # Check if the user is a lecturer
            return Module.objects.filter(lecturer=user.lecturer)
        return Module.objects.none()  # Prevent unauthorized users

class AssignmentListCreate(generics.ListCreateAPIView):
    """
    API view to list and create assignments for a specific module.
    Only lecturers associated with the module can perform these actions.
    """
    serializer_class = AssignmentSerializer
    permission_classes = [IsAuthenticated]  # Ensure only authenticated users can access this view

    def get_queryset(self):
        user = self.request.user
        module_id = self.request.query_params.get('module_id')  # Get the module_id from the query parameters

        if module_id and hasattr(user, 'lecturer'):  # Check if the user is a lecturer
            # Fetch assignments for the specified module owned by the lecturer
            return Assignment.objects.filter(module__lecturer=user.lecturer, module__id=module_id)
        
        # If no module_id or unauthorized access, return empty queryset
        return Assignment.objects.none()

    def perform_create(self, serializer):
        """
        Create a new assignment under the module the lecturer owns.
        """
        user = self.request.user
        module_id = self.request.data.get("module_id")
        try:
            # Check if the lecturer owns the specified module
            module = Module.objects.get(id=module_id, lecturer=user.lecturer)
            # Save the assignment with the module
            serializer.save(module=module)
        except Module.DoesNotExist:
            raise Exception("You do not have permission to add assignments to this module.")

class AssignmentListView(generics.ListAPIView):
    """
    API view to fetch all assignments for the modules owned by the authenticated lecturer.
    """
    serializer_class = AssignmentSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
            user = self.request.user
            module_id = self.request.query_params.get('module_id')  # Get the module_id from the query parameters

            if module_id and hasattr(user, 'lecturer'):  # Check if the user is a lecturer
                # Fetch assignments for the specified module owned by the lecturer
                return Assignment.objects.filter(module__lecturer=user.lecturer, module__id=module_id)
            
            # If no module_id or unauthorized access, return empty queryset
            return Assignment.objects.none()
    
class AssignmentDetailView(generics.RetrieveAPIView):
    """
    API view to fetch a specific assignment.
    Only the lecturer who owns the module can access this view.
    """
    serializer_class = AssignmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'lecturer'):  # Check if the user is a lecturer
            # Fetch assignments for modules owned by the lecturer
            return Assignment.objects.filter(module__lecturer=user.lecturer)
        return Assignment.objects.none()  # Prevent unauthorized users
    
class AssignmentDeleteView(generics.DestroyAPIView):
    """
    API view to delete an assignment.
    Only the lecturer associated with the module can delete its assignments.
    """
    serializer_class = AssignmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'lecturer'):  # Check if the user is a lecturer
            # Fetch assignments for modules owned by the lecturer
            return Assignment.objects.filter(module__lecturer=user.lecturer)
        return Assignment.objects.none()  # Prevent unauthorized users


class AssignmentUpdateView(generics.UpdateAPIView):
    """
    API view to update an assignment.
    Only the lecturer associated with the module can update its assignments.
    """
    serializer_class = AssignmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'lecturer'):  # Check if the user is a lecturer
            # Fetch assignments for modules owned by the lecturer
            return Assignment.objects.filter(module__lecturer=user.lecturer)
        return Assignment.objects.none()  # Prevent unauthorized users
    

class FileUploadView(generics.CreateAPIView):
    """
    Handles multiple file uploads for a specific assignment.
    """
    serializer_class = FileUploadSerializer

    def create(self, request, *args, **kwargs):
        submission_id = kwargs.get('submission_id')
        files = request.FILES.getlist('files')  # Extract multiple files from request

        if not files:
            return Response({"error": "No files uploaded."}, status=status.HTTP_400_BAD_REQUEST)

        existing_files = []  # To store names of files already uploaded
        new_submissions = []  # To store new submissions

        for file in files:
            # Calculate a hash of the file content (MD5 or SHA256)
            file_hash = self.calculate_file_hash(file)

            # Check if the file already exists in the database based on the hash value
            existing_submission = Submission.objects.filter(file_hash=file_hash, assignment_id=submission_id).first()

            if existing_submission:
                # If file already exists, add to the skipped list
                existing_files.append(file.name)
            else:
                # If it's a new file, save the submission
                submission = Submission.objects.create(
                    assignment_id=submission_id, 
                    file=file,
                    file_hash=file_hash  # Store the file hash in the database to prevent future duplicates
                )
                new_submissions.append(submission)

        # Prepare response message
        message = {}
        if existing_files:
            message['skipped_files'] = existing_files

        if new_submissions:
            # If there are new submissions, serialize and return them
            serializer = self.get_serializer(new_submissions, many=True)
            message['new_files'] = serializer.data

        if not message:
            return Response({"message": "No new files uploaded."}, status=status.HTTP_400_BAD_REQUEST)

        return Response(message, status=status.HTTP_201_CREATED)

    def calculate_file_hash(self, file):
        """Calculate the hash of the file content."""
        hash_obj = hashlib.md5()  # You can also use hashlib.sha256()
        for chunk in file.chunks():
            hash_obj.update(chunk)
        return hash_obj.hexdigest()


#class GradeSubmissionView(generics.UpdateAPIView):
    queryset = Submission.objects.all()
    serializer_class = ScoreUpdateSerializer

    def update(self, request, *args, **kwargs):
        assignment_id = kwargs.get("assignment_id")
        submissions = Submission.objects.filter(assignment_id=assignment_id)
       
        # Fetch the marking scheme
        marking_scheme = get_markingScheme(assignment_id)
        if not marking_scheme:
            return Response({"error": "Marking scheme not found for this assignment."}, status=404)

        # Grade each submission
        for submission in submissions:
            submission.score = grade_submission(submission, marking_scheme)
            submission.save()

        # Return only scores
        scores = [{"id": submission.id, "score": submission.score} for submission in submissions]
        return Response(scores)

class GradeSubmissionView(generics.UpdateAPIView):
    queryset = Submission.objects.all()
    serializer_class = ScoreUpdateSerializer

    def update(self, request, *args, **kwargs):
        assignment_id = kwargs.get("assignment_id")
        submissions = Submission.objects.filter(assignment_id=assignment_id)
       
        # Fetch the marking scheme
        marking_scheme = get_markingScheme(assignment_id)
        if not marking_scheme:
            return Response({"error": "Marking scheme not found for this assignment."}, status=404)

        # Grade each submission
        scores = []
        for submission in submissions:
            # This will use existing results if available
            total_score = grade_submission(submission, marking_scheme)
            scores.append({"id": submission.id, "score": total_score, "file_name": submission.file_name})

        return Response(scores)
    
class GradingResultListView(generics.ListAPIView):
    """
    API view to fetch all grading results for a specific submission.
    """
    serializer_class = GradingResultSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        submission_id = self.kwargs.get('submission_id')
        return GradingResult.objects.filter(submission_id=submission_id)
    
class ClearGradingResultsView(APIView):
    """
    API view to clear all grading results for a specific assignment
    and force regrading on the next request.
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request, assignment_id):
        # Get all submissions for the assignment
        submissions = Submission.objects.filter(assignment_id=assignment_id)
        
        # Get all grading results for these submissions
        grading_results = GradingResult.objects.filter(submission__in=submissions)
        
        # Count how many were deleted
        count = grading_results.count()
        
        # Delete all grading results
        grading_results.delete()
        
        # Reset scores in submissions to trigger recalculation
        submissions.update(score=None)
        
        return Response({
            "message": f"Successfully cleared {count} grading results for assignment {assignment_id}.",
            "submissions_affected": submissions.count()
        })

   
  
class FileListView(generics.ListAPIView):
    """
    API view to fetch all files uploaded for a specific assignment.
    """
    serializer_class = FileListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        assignment_id = self.kwargs.get('assignment_id')
        return Submission.objects.filter(assignment_id=assignment_id)
    

class DeleteFileView(generics.DestroyAPIView):
    """
    Handle file deletion for a specific submission.
    """
    serializer_class = FileUploadSerializer
    permission_classes = [IsAuthenticated]
    queryset = Submission.objects.all()
    lookup_field = "id"  # Adjust this to the primary key field used for lookup

    def delete(self, request, submission_id, fileId):
        try:
            submission = Submission.objects.get(assignment_id=submission_id, id=fileId)
            submission.file.delete()  # Delete the actual file
            submission.delete()       # Delete the database record
            return Response({"success": "File deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except Submission.DoesNotExist:
            return Response({"error": "File not found."}, status=status.HTTP_404_NOT_FOUND)

class FileDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, assignment_id, file_id):
        # Fetch the submission (uploaded file)
        try:
            submission = Submission.objects.get(id=file_id, assignment_id=assignment_id)
        except Submission.DoesNotExist:
            return Response({"error": "Submission not found."}, status=404)

        # Fetch the marking scheme for the assignment
        marking_scheme = get_markingScheme(assignment_id)
        if not marking_scheme:
            return Response({"error": "Marking scheme not found for this assignment."}, status=404)

        # Get the detailed grading information using our optimized function
        # This will use existing results if available
        answers_details = get_answer_details(submission, marking_scheme)
        
        # Get or calculate the total score
        # This will also use existing results if available
        total_score = grade_submission(submission, marking_scheme)

        # Prepare the response data
        response_data = {
            "file": submission.file.url,
            "file_name": submission.file_name,
            "answers": answers_details,
            "marking_scheme": marking_scheme,
            "score": total_score,
        }

        return Response(response_data)
    

class MarkingSchemeRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    Handle GET, PUT, and DELETE requests for a specific MarkingScheme.
    """
    serializer_class = MarkingSchemeSerializer

    def get_object(self):
        assignment_id = self.kwargs.get("assignment_id")
        try:
            return MarkingScheme.objects.get(assignment_id=assignment_id)
        except MarkingScheme.DoesNotExist:
            raise NotFound(detail="Marking scheme not found.")

class MarkingSchemeCreateView(generics.CreateAPIView):
    """
    Handle POST requests to create a new MarkingScheme.
    """
    serializer_class = MarkingSchemeSerializer

    def create(self, request, *args, **kwargs):
        assignment_id = self.kwargs.get("assignment_id")
        request.data['assignment'] = assignment_id  # Add assignment ID to the request data
        return super().create(request, *args, **kwargs)


logger = logging.getLogger(__name__)

class ParseMarkingSchemeView(APIView):
    """
    API view to parse marking scheme from uploaded files.
    Handles automatic extraction of questions, answers, and grading options.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request, assignment_id):
        """
        Handle file upload and parse content into marking scheme items.
        """
        if 'file' not in request.FILES:
            return Response({"error": "No file provided"}, status=400)
            
        uploaded_file = request.FILES['file']
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            for chunk in uploaded_file.chunks():
                temp_file.write(chunk)
                
        try:
            # Extract text from the file based on its format
            file_extension = os.path.splitext(uploaded_file.name)[1].lower()
            file_content = self.extract_text_from_file(temp_file.name, file_extension)
            
            # Parse the content with Ollama
            parsed_items = self.parse_with_ollama(file_content)
            
            # Process the parsed items
            processed_items = self.process_parsed_items(parsed_items)
            
            # Clean up temporary file
            os.unlink(temp_file.name)
            
            return Response({'items': processed_items})
            
        except Exception as e:
            # Clean up temporary file in case of error
            os.unlink(temp_file.name)
            logger.error(f"Error parsing marking scheme file: {str(e)}")
            return Response({"error": str(e)}, status=500)

    def extract_text_from_file(self, file_path, file_extension):
        """Extract text from different file types."""
        if file_extension == '.docx':
            # Use the existing document parsing logic from functions.py
            from docx import Document
            doc = Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
            
        elif file_extension == '.pdf':
            # Use the existing PDF parsing logic
            from PyPDF2 import PdfReader
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
            
        elif file_extension == '.xlsx':
            import pandas as pd
            df = pd.read_excel(file_path)
            
            # Try to detect relevant columns
            headers = [str(col).lower() for col in df.columns]
            text_representation = ""
            
            # Check if we can identify question/answer columns
            q_col = next((i for i, h in enumerate(headers) if any(x in h for x in ['question', 'prompt'])), None)
            a_col = next((i for i, h in enumerate(headers) if any(x in h for x in ['answer', 'response', 'solution'])), None)
            m_col = next((i for i, h in enumerate(headers) if any(x in h for x in ['mark', 'score', 'point'])), None)
            
            # Format as text for the AI to process
            for idx, row in df.iterrows():
                line = f"{idx+1}. "
                if q_col is not None and pd.notna(row.iloc[q_col]):
                    line += f"Question: {row.iloc[q_col]} "
                if a_col is not None and pd.notna(row.iloc[a_col]):
                    line += f"Answer: {row.iloc[a_col]} "
                if m_col is not None and pd.notna(row.iloc[m_col]):
                    line += f"Marks: {row.iloc[m_col]}"
                text_representation += line + "\n"
                
            return text_representation
            
        elif file_extension == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
                
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
    
    def parse_with_ollama(self, content):
        """Use Ollama to parse the content into structured marking scheme data."""
        system_prompt = """
        You are an expert at analyzing educational content and creating marking schemes. Your task is to output a structured marking scheme(json string) from the provided content.
        
        Please extract:
        1. Question number (required)
        2. Question text if present
        3. Answer text (required)
        4. Marks/points value if specified
        5. Appropriate grading type based on the answer if specified
        
        For grading types:
        - "one-word": Use for single word or very short (1-2 words) answers
        - "short-phrase": Use for sentence answers that require meaning comparison
        - "list": Use when the answer contains multiple items with comma-separated values looks like list
        - "numerical": Use for numbers, calculations, or numeric ranges
        
        Return a well-structured JSON array with each question as an object. Include all the information you have extracted. If no marks are specified, omit the "marks" field. If no question text is available, include an empty string for "question".
        
        Output format:
        [
          {
            "number": 1,
            "question": "What is the capital of France?",
            "answer": "Paris",
            "marks": 5,
            "gradingType": "one-word"
          },
          ...
        ]
        
        If marks are not specified, omit the "marks" field. If question text isn't available, include an empty string for "question".
        """
        
        user_prompt = f"""
        Please create a structured marking scheme from the following content. Extract all questions and answers:
        
        {content}
        
        Return only JSON with no additional text.
        """
        
        try:
            # Use the existing Ollama integration from functions.py
            response = ollama.chat(
                model="qwen2.5:1.5b",  # Using the model specified in your existing code
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                 options={
                "num_gpu": 0,          # Force CPU inference for stability
                "num_thread": 4,        # Match thread count to available CPU
                "mirostat": 0,          # Disable mirostat sampling
                "top_k": 50,            # Limit vocabulary sampling for speed
                "repeat_penalty": 1.1   # Lower repeat penalty for faster generation
                }
            )
            
            # Extract the JSON response
            response_content = response["message"]["content"].strip()
            
            # Try to extract just the JSON array
            json_match = re.search(r'\[\s*\{.*\}\s*\]', response_content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            else:
                # Try parsing the entire content as JSON
                return json.loads(response_content)
                
        except Exception as e:
            logger.error(f"Error parsing with Ollama: {e}")
            # If parsing fails, try a more structured approach
            return self.fallback_parsing(content)
    
    def fallback_parsing(self, content):
        """Fallback method if the AI parsing fails, using regex patterns."""
        items = []
        
        # Common patterns for numbered items
        patterns = [
            r'(\d+)[.)]?\s+(.+?)(?=\n\d+[.)]|\Z)',  # Standard numbered format: "1. Answer"
            r'Q(?:uestion)?\s*(\d+)[.:]?\s+(.+?)(?=Q(?:uestion)?\s*\d+|$)',  # Q1 format
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, content, re.DOTALL)
            for match in matches:
                number = int(match.group(1))
                answer_text = match.group(2).strip()
                
                # Skip if already found this question number
                if any(item['number'] == number for item in items):
                    continue
                    
                # Look for marks in the answer text
                marks_match = re.search(r'\((\d+)\s*marks?\)', answer_text, re.IGNORECASE)
                marks = None
                if marks_match:
                    marks = int(marks_match.group(1))
                    # Remove the marks text from the answer
                    answer_text = re.sub(r'\((\d+)\s*marks?\)', '', answer_text).strip()
                
                # Basic item with defaults
                item = {
                    'number': number,
                    'question': "",
                    'answer': answer_text,
                }
                
                if marks:
                    item['marks'] = marks
                
                # Try to infer grading type
                if re.match(r'^\d+(\.\d+)?$', answer_text):
                    item['gradingType'] = 'numerical'
                elif ',' in answer_text and len(answer_text.split(',')) > 1:
                    item['gradingType'] = 'list'
                elif len(answer_text.split()) > 3:
                    item['gradingType'] = 'short-phrase'
                else:
                    item['gradingType'] = 'one-word'
                
                items.append(item)
        
        return items
    
    def process_parsed_items(self, parsed_items):
        """Process parsed items and apply defaults where needed."""
        processed_items = []
        
        for item in parsed_items:
            # Skip items without required fields
            if 'number' not in item or 'answer' not in item:
                continue
                
            # Ensure the answer is not empty
            if not item.get('answer', '').strip():
                continue
                
            # Create a new item with defaults
            processed_item = {
                'number': item.get('number'),
                'question': item.get('question', ""),
                'answer': item.get('answer'),
                'marks': item.get('marks', 10),  # Default to 10 marks as specified
                'gradingType': item.get('gradingType', 'one-word')
            }
            
            # Set smart defaults based on content
            if processed_item['gradingType'] == 'one-word':
                # If answer has capital letters, make it case sensitive
                processed_item['caseSensitive'] = any(c.isupper() for c in processed_item['answer'])
            elif processed_item['gradingType'] == 'list':
                processed_item['partialMatching'] = True  # Enable partial matching for lists
            elif processed_item['gradingType'] == 'numerical':
                processed_item['rangeSensitive'] = False  # Enable range for numerical
            
            processed_items.append(processed_item)
        
        return processed_items 


class AssignmentReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, assignment_id):
        """
        API view to fetch the report data (statistics and grades) for a specific assignment.
        """

        # Fetch the submissions for the given assignment
        submissions = Submission.objects.filter(assignment_id=assignment_id)

        # Fetch all the grades (scores) for this assignment
        grades = submissions.values_list('score', flat=True)

        if not grades:
            return Response({"message": "No grades found for this assignment."}, status=404)

        # Calculate statistics (highest, lowest, median, average)
        highest = max(grades)
        lowest = min(grades)
        median = np.median(grades)
        print("median", median)
        average = sum(grades) / len(grades)

        # Count the number of passed and failed submissions (assuming 45 is the pass mark)
        passed = sum(1 for grade in grades if grade >= 45)
        failed = len(grades) - passed

        # Prepare the response data
        report_data = {
            "highest": highest,
            "lowest": lowest,
            "median": median,
            "average": average,
            "passed": passed,
            "failed": failed,
            "grades": list(grades),
        }

        return Response(report_data)   






# View related to the Lecturer and Student
# Create your views here.
class GetLecturerView(generics.ListAPIView):
    queryset = Lecturer.objects.all()
    serializer_class = LecturerSerializer
    permission_classes = [AllowAny]
 
class CreateLecturerView(generics.CreateAPIView):
    queryset = Lecturer.objects.all()
    serializer_class = LecturerSerializer
    permission_classes = [AllowAny]

class LecturerDetailView(generics.RetrieveUpdateAPIView):
    queryset = Lecturer.objects.all()
    serializer_class = LecturerDetailSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]  # Add this to support FormData

    def get_object(self):
        user = self.request.user
        try:
            return Lecturer.objects.get(user=user)
        except Lecturer.DoesNotExist:
            raise NotFound(detail="Lecturer not found")

    def update(self, request, *args, **kwargs):
        mutable_data = request.data.copy()

        # Parse 'user' JSON string to dict
        if 'user' in mutable_data:
            try:
                mutable_data['user'] = json.loads(mutable_data['user'])
            except json.JSONDecodeError:
                return Response({"error": "Invalid JSON in 'user'"}, status=400)

        # Pass the parsed, mutable data to the serializer
        serializer = self.get_serializer(self.get_object(), data=mutable_data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

class LecturerProfileView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        """Get the lecturer profile information"""
        try:
            lecturer = Lecturer.objects.get(user=request.user)

            profile_picture_url = None
            if lecturer.profile_picture:
                # Get the base URL from your settings
                base_url = request.build_absolute_uri('/').rstrip('/')
                # Construct the correct media URL
                profile_picture_url = f"{base_url}/media/{lecturer.profile_picture}"
                # Format the response to match what frontend expects
            response_data = {
                "user_info": {
                    "id": request.user.id,
                    "username": request.user.username,
                    "email": request.user.email,
                    "first_name": request.user.first_name,
                    "last_name": request.user.last_name,
                },
                "university": lecturer.university,
                "department": lecturer.department,
                "profile_picture": profile_picture_url
            }
            return Response(response_data)
        except Lecturer.DoesNotExist:
            return Response({"detail": "Lecturer profile not found."}, status=404)
    
    def patch(self, request):
        """Update the lecturer profile (university, department)"""
        try:
            lecturer = Lecturer.objects.get(user=request.user)
            
            # Get the data from the request
            university = request.data.get('university')
            department = request.data.get('department')
            
            # Update the lecturer object
            if university is not None:
                lecturer.university = university
            if department is not None:
                lecturer.department = department
                
            lecturer.save()
            
            # Return updated profile
            response_data = {
                "university": lecturer.university,
                "department": lecturer.department,
                "detail": "Academic information updated successfully"
            }
            
            return Response(response_data)
        except Lecturer.DoesNotExist:
            return Response({"detail": "Lecturer profile not found."}, status=404)


class UserProfileView(APIView):
    """View for updating user information (first_name, last_name, email)"""
    permission_classes = [IsAuthenticated]
    
    def patch(self, request):
        """Update the user profile"""
        user = request.user
        
        # Get data from request
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        email = request.data.get('email')
        
        # Update fields if provided
        if first_name is not None:
            user.first_name = first_name
        if last_name is not None:
            user.last_name = last_name
        if email is not None:
            user.email = email
            
        user.save()
        
        # Return updated data
        return Response({
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "detail": "Profile information updated successfully"
        })

class PasswordChangeView(APIView):
    """View for changing user password"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')
        
        # Validate input
        if not current_password or not new_password or not confirm_password:
            return Response({"detail": "All password fields are required"}, status=400)
            
        if new_password != confirm_password:
            return Response({"confirm_password": "Passwords do not match."}, status=400)
            
        # Verify current password
        user = request.user
        if not user.check_password(current_password):
            return Response({"current_password": "Incorrect password."}, status=400)
            
        # Set new password
        user.set_password(new_password)
        user.save()
        
        return Response({"detail": "Password changed successfully."})

class ProfilePictureView(APIView):
    """View for uploading a profile picture"""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def post(self, request):
        try:
            lecturer = Lecturer.objects.get(user=request.user)
            
            if 'profile_picture' not in request.FILES:
                return Response({"detail": "No file was submitted."}, status=400)
                
            # Delete old profile picture if it exists
            if lecturer.profile_picture:
                lecturer.profile_picture.delete(save=False)
                
            # Save new profile picture
            lecturer.profile_picture = request.FILES['profile_picture']
            lecturer.save()
            
            return Response({
                "detail": "Profile picture updated successfully.",
                "profile_picture": request.build_absolute_uri(lecturer.profile_picture.url) if lecturer.profile_picture else None
            })
            
        except Lecturer.DoesNotExist:
            return Response({"detail": "Lecturer profile not found."}, status=404)
  
# View for creating a Student
class CreateStudentView(generics.CreateAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [AllowAny]


class AssignmentListPageView(generics.ListAPIView):
    serializer_class = AssignmentPageSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None  # Disable pagination if not needed

    def get_queryset(self):
        user = self.request.user
        # First, ensure the user only sees their own assignments
        if hasattr(user, 'lecturer'):
            queryset = Assignment.objects.filter(module__lecturer=user.lecturer)
        else:
            return Assignment.objects.none()
        
        # Apply filters from query parameters
        module_id = self.request.query_params.get('module')
        if module_id and module_id != 'all':
            queryset = queryset.filter(module_id=module_id)
            
        # Apply search if provided
        search_query = self.request.query_params.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) | 
                Q(description__icontains=search_query)
            )
            
        # Apply sorting
        sort_by = self.request.query_params.get('sort_by', 'created_at')
        sort_order = self.request.query_params.get('sort_order', 'asc')
        
        # Validate sort_by field to prevent injection
        valid_sort_fields = ['title', 'created_at', 'due_date']
        if sort_by not in valid_sort_fields:
            sort_by = 'created_at'
            
        # Apply sort direction
        if sort_order == 'desc':
            sort_by = f'-{sort_by}'
            
        return queryset.order_by(sort_by)




def get_module_trends(request):
    """
    Fetch the count of modules created per day.
    """
    module_data = (
        Module.objects.annotate(day=TruncDay("created_at"))  # Truncates to day
        .values("day")
        .annotate(count=Count("id"))
        .order_by("day")
    )
    # Convert data to desired JSON format
    response_data = [
        {"day": data["day"].strftime("%Y-%m-%d"), "count": data["count"]}  # Date and count
        for data in module_data
    ]
    return JsonResponse(response_data, safe=False)


def get_assignment_trends(request):
    """
    Fetch the count of assignments created per day.
    """
    assignment_data = (
        Assignment.objects.annotate(day=TruncDay("created_at"))  # Truncates to day
        .values("day")
        .annotate(count=Count("id"))
        .order_by("day")
    )
    response_data = [
        {"day": data["day"].strftime("%Y-%m-%d"), "count": data["count"]}  # Date and count
        for data in assignment_data
    ]
    return JsonResponse(response_data, safe=False)


def get_upload_trends(request):
    """
    Fetch the count of uploads created per day.
    """
    upload_data = (
        Submission.objects.annotate(day=TruncDay("uploaded_at"))  # Truncates to day
        .values("day")
        .annotate(count=Count("id"))
        .order_by("day")
    )
    response_data = [
        {"day": data["day"].strftime("%Y-%m-%d"), "count": data["count"]}  # Date and count
        for data in upload_data
    ]
    return JsonResponse(response_data, safe=False)