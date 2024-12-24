import stat
from rest_framework.response import Response
from django.shortcuts import render
from django.contrib.auth.models import User
from rest_framework import generics
from .serializers import LecturerSerializer, StudentSerializer, ModuleSerializer, AssignmentSerializer,  ScoreUpdateSerializer  , FileUploadSerializer, MarkingSchemeSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Lecturer, Student, Module, Assignment, Submission  , MarkingScheme
from rest_framework import status
import hashlib


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
    """
    Updates the scores for submissions of a specific assignment.
    """
    queryset = Submission.objects.all()
    serializer_class = ScoreUpdateSerializer

    def update(self, request, *args, **kwargs):
        assignment_id = kwargs.get('assignment_id')
        submissions = Submission.objects.filter(assignment_id=assignment_id)

        if not submissions.exists():
            return Response({"error": "No submissions found for this assignment."}, status=stat.HTTP_404_NOT_FOUND)

        # Simulate score generation and update submissions
        for submission in submissions:
            submission.score = self.generate_score(submission.file)  # Custom scoring logic
            submission.save()

        serializer = self.get_serializer(submissions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def generate_score(self, file):
        # Dummy scoring logic (replace with actual logic)
        return len(file.name) % 100
    
class FileListView(generics.ListAPIView):
    """
    API view to fetch all files uploaded for a specific assignment.
    """
    serializer_class = FileUploadSerializer
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
        

class MarkingSchemeListCreateView(generics.ListCreateAPIView):
    queryset = MarkingScheme.objects.all()
    serializer_class = MarkingSchemeSerializer

class MarkingSchemeRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MarkingScheme.objects.all()
    serializer_class = MarkingSchemeSerializer



# Create your views here.
class GetLecturerView(generics.ListAPIView):
    queryset = Lecturer.objects.all()
    serializer_class = LecturerSerializer
    permission_classes = [AllowAny]
    
class CreateLecturerView(generics.CreateAPIView):
    queryset = Lecturer.objects.all()
    serializer_class = LecturerSerializer
    permission_classes = [AllowAny]

# View for creating a Student
class CreateStudentView(generics.CreateAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [AllowAny]