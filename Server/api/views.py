import stat
from urllib import response
from django.shortcuts import render
from django.contrib.auth.models import User
from rest_framework import generics
from .serializers import LecturerSerializer, StudentSerializer, ModuleSerializer, AssignmentSerializer,  ScoreUpdateSerializer  , FileUploadSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Lecturer, Student, Module, Assignment, Submission  


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
        assignment_id = kwargs.get('assignment_id')
        files = request.FILES.getlist('files')  # Extract multiple files from request

        if not files:
            return response({"error": "No files uploaded."}, status=stat.HTTP_400_BAD_REQUEST)

        submissions = []
        for file in files:
            submission = Submission.objects.create(assignment_id=assignment_id, file=file)
            submissions.append(submission)

        serializer = self.get_serializer(submissions, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    

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
            return response({"error": "No submissions found for this assignment."}, status=stat.HTTP_404_NOT_FOUND)

        # Simulate score generation and update submissions
        for submission in submissions:
            submission.score = self.generate_score(submission.file)  # Custom scoring logic
            submission.save()

        serializer = self.get_serializer(submissions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def generate_score(self, file):
        # Dummy scoring logic (replace with actual logic)
        return len(file.name) % 100




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