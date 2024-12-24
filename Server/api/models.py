from django.db import models
from django.contrib.auth.models import User


# Lecturer model
class Lecturer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    University = models.CharField(max_length=100 ,null=True)
    Department = models.CharField(max_length=100, null=True)
    def __str__(self):
        return self.lecturer_name


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
    code = models.CharField(max_length=20, unique=True)  # Unique code for the module
    description = models.TextField(blank=True, null=True)
    lecturer = models.ForeignKey(Lecturer, on_delete=models.CASCADE, related_name="modules")  
    
    def __str__(self):
        return f"{self.name} ({self.code})"

# Model representing an assignment within a module
class Assignment(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    due_date = models.DateTimeField()
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="assignments")

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

class MarkingScheme(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="marking_schemes")
    title = models.CharField(max_length=255, help_text="Title of the marking scheme")
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
    answer_text = models.TextField(help_text="The text of the answer")
    marks = models.PositiveIntegerField(help_text="Marks allocated for this answer")

    def __str__(self):
        return f"Answer {self.id} for {self.marking_scheme.title}"