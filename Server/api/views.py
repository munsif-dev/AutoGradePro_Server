import json
import re
import stat
from rest_framework.response import Response
from django.shortcuts import render
from django.contrib.auth.models import User
from rest_framework import generics
from .serializers import AssignmentPageSerializer, FileListSerializer, LecturerSerializer, UserSerializer, StudentSerializer, ModuleSerializer, AssignmentSerializer,  ScoreUpdateSerializer  , FileUploadSerializer, MarkingSchemeSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from .models import Lecturer, Student, Module, Assignment, Submission  , MarkingScheme
from rest_framework import status
import hashlib
from rest_framework.exceptions import NotFound
from django.db.models.functions import TruncMonth
from django.db.models import Count, Q
from django.http import JsonResponse
from rest_framework.filters import OrderingFilter, SearchFilter
from PyPDF2 import PdfReader
from docx import Document
import numpy as np
from .functions  import  get_markingScheme,get_answer_details, grade_submission, parse_submission_file, is_answer_correct, parse_txt_file, parse_pdf_file, parse_docx_file, extract_answers_from_text, normalize_answer



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
        for submission in submissions:
            submission.score = grade_submission(submission, marking_scheme)
            submission.save()

        # Return only scores
        scores = [{"id": submission.id, "score": submission.score} for submission in submissions]
        return Response(scores)

   
  
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

        # Parse the answers from the submission file
        try:
            submission_answers = parse_submission_file(submission.file)
        except Exception as e:
            print(f"Error reading submission file: {e}")
            return Response({"error": "Error reading submission file."}, status=500)

        # Grade the submission
        total_score = grade_submission(submission, marking_scheme)

         # Prepare the response data with the new format
        answers_details = get_answer_details(submission, marking_scheme)


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

class UserDetailsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get the current logged-in user
        user = request.user
        # Serialize the user data
        serializer = UserSerializer(user)
        return Response(serializer.data)
    
class CreateLecturerView(generics.CreateAPIView):
    queryset = Lecturer.objects.all()
    serializer_class = LecturerSerializer
    permission_classes = [AllowAny]

class LecturerUpdateView(generics.UpdateAPIView):
    """
    API view to update user details including first name, last name, email, and password.
    """
    serializer_class = LecturerSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user.lecturer

    def update(self, request, *args, **kwargs):
        user = request.user
        data = request.data

        if 'password' in data:
            user.set_password(data['password'])
            user.save()

        return super().update(request, *args, **kwargs)
    
class UploadProfilePictureView(generics.UpdateAPIView):
    """
    API view to upload a profile picture for a lecturer.
    """
    serializer_class = LecturerSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user.lecturer

    def update(self, request, *args, **kwargs):
        lecturer = self.get_object()
        lecturer.profile_picture = request.FILES.get('profile_picture')
        lecturer.save()
        return Response({'message': 'Profile picture updated successfully'}, status=status.HTTP_200_OK)


# View for creating a Student
class CreateStudentView(generics.CreateAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [AllowAny]

class AssignmentListPageView(generics.ListAPIView):

    queryset = Assignment.objects.all()
    serializer_class = AssignmentPageSerializer
    filter_backends = (SearchFilter, OrderingFilter)
    search_fields = ['title', 'description']  # Fields to search by
    ordering_fields = ['created_at', 'title']  # Fields that can be sorted
    ordering = ['created_at']  # Default ordering

    def get_queryset(self):
        """
        Optionally restricts the returned assignments by filtering against
        a `search` query parameter and applying sorting.
        """
        queryset = super().get_queryset()  # Use the default queryset

        # Apply search query filtering
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) | Q(description__icontains=search_query)
            )

        # Handle the sorting manually (if needed)
        sort_by = self.request.GET.get('sort_by', 'created_at')
        sort_order = self.request.GET.get('sort_order', 'asc')

        if sort_order == 'desc':
            sort_by = f'-{sort_by}'

        queryset = queryset.order_by(sort_by)  # Apply sorting based on the provided parameters
        return queryset
    






# Function based views for fetching trends

def get_module_trends(request):
    """
    Fetch the count of modules created per month.
    """
    module_data = (
        Module.objects.annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(count=Count("id"))
        .order_by("month")
    )
    # Convert data to desired JSON format
    response_data = [
        {"month": data["month"].strftime("%B %Y"), "count": data["count"]}
        for data in module_data
    ]
    return JsonResponse(response_data, safe=False)


def get_assignment_trends(request):
    """
    Fetch the count of assignments created per month.
    """
    assignment_data = (
        Assignment.objects.annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(count=Count("id"))
        .order_by("month")
    )
    response_data = [
        {"month": data["month"].strftime("%B %Y"), "count": data["count"]}
        for data in assignment_data
    ]
    return JsonResponse(response_data, safe=False)


def get_upload_trends(request):
    """
    Fetch the count of uploads created per month.
    """
    upload_data = (
        Submission.objects.annotate(month=TruncMonth("uploaded_at"))
        .values("month")
        .annotate(count=Count("id"))
        .order_by("month")
    )
    response_data = [
        {"month": data["month"].strftime("%B %Y"), "count": data["count"]}
        for data in upload_data
    ]
    return JsonResponse(response_data, safe=False)



