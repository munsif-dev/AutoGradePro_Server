from django.db import models
from django.contrib.auth.models import User


# Lecturer model

class Lecturer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    university = models.CharField(max_length=100, null=True)
    department = models.CharField(max_length=100, null=True)
    profile_picture = models.ImageField(upload_to="profile_pictures/", null=True, blank=True)

    def get_profile_picture_url(self, request=None):
        if not self.profile_picture:
            return None
        
        if request:
            return request.build_absolute_uri(self.profile_picture.url)
        else:
            # Fallback when request is not available
            from django.conf import settings
            return settings.MEDIA_URL + self.profile_picture.name

    def __str__(self):
        return self.user.username  # Ensure a meaningful string representation



# Student model
class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    University = models.CharField(max_length=100, null=True)
    Index_number = models.CharField(max_length=100, null=True)
    

    def __str__(self):
        return self.student_name


# Model representing a module
class Module(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=20, unique=False)  # Unique code for the module
    description = models.TextField(blank=True, null=True)
    lecturer = models.ForeignKey(Lecturer, on_delete=models.CASCADE, related_name="modules")  
    created_at = models.DateTimeField(auto_now_add=True) 
    
    def __str__(self):
        return f"{self.name} ({self.code})"

# Model representing an assignment within a module
class Assignment(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    due_date = models.DateTimeField()
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="assignments")
    created_at = models.DateTimeField(auto_now_add=True) 

    def __str__(self):
        return f"{self.title} - {self.module.name}"

# Model representing files uploaded by the lecturer for an assignment
class Submission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="files")
    file = models.FileField(upload_to="assignments/%Y/%m/%d/")  # Path where files will be stored
    file_name = models.CharField(max_length=255, blank=True, null=True)  # To store file name
    file_hash = models.CharField(max_length=64, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    score = models.IntegerField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.file and not self.file_name:
            self.file_name = self.file.name  # Automatically set the file name
        super().save(*args, **kwargs)

    def __str__(self):
        return f"File for {self.assignment.title} uploaded at {self.uploaded_at}"
    
# Model representing marking scheme for an assignment
class MarkingScheme(models.Model):
    assignment = models.OneToOneField(
        Assignment, 
        on_delete=models.CASCADE, 
        related_name="marking_scheme"
    )
    title = models.CharField(max_length=255, help_text="Title of the marking scheme")
    pass_score = models.PositiveIntegerField(
        default=40, 
        help_text="Minimum score required to pass"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class Answer(models.Model):
    marking_scheme = models.ForeignKey(
        MarkingScheme, 
        on_delete=models.CASCADE, 
        related_name="answers"
    )
    question_text = models.TextField(help_text="The text of the question", blank=True, null=True)
    answer_text = models.TextField(help_text="The text of the answer")
    marks = models.PositiveIntegerField(help_text="Marks allocated for this answer")
    grading_type = models.CharField(
        max_length=20, 
        choices=[
            ('one-word', 'One Word'),
            ('short-phrase', 'Short Phrase'),
            ('list', 'List'),
            ('numerical', 'Numerical')
        ], 
        default='one-word'
    )
    case_sensitive = models.BooleanField(default=False)
    order_sensitive = models.BooleanField(default=False)
    range_sensitive = models.BooleanField(default=False)
    partial_matching = models.BooleanField(default=False, help_text="For list type answers, allow partial credit for partially correct lists")
    semantic_threshold = models.FloatField(default=0.7, help_text="Threshold for semantic matching (0-1) for short-phrase answers")
    range = models.JSONField(
        default=dict, 
        null=True,
        blank=True, 
        help_text="Range for numerical answers, e.g., {'min': 0, 'max': 100, 'tolerance_percent': 5}"
    )

    def __str__(self):
        return f"Answer {self.id} for {self.marking_scheme.title}"


# Add this to models.py
class GradingResult(models.Model):
    submission = models.ForeignKey(
        Submission, 
        on_delete=models.CASCADE, 
        related_name="grading_results"
    )
    question_id = models.IntegerField()
    student_answer = models.TextField()
    correct_answer = models.TextField()
    marks_awarded = models.IntegerField(default=0)
    allocated_marks = models.IntegerField()
    grading_type = models.CharField(max_length=20)
    is_correct = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('submission', 'question_id')
        
    def __str__(self):
        return f"Q{self.question_id} for {self.submission.file_name}"