from rest_framework import serializers
from django.contrib.auth.models import User  # Import Django's built-in User model
from .models import Lecturer
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Lecturer, Student, Module, Assignment, Submission


# UserSerializer (handles user creation and updating)
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'email', 'first_name', 'last_name']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)  # Create a new user with hashed password
        return user


# LecturerSerializer (handles creation of Lecturer with linked User)
class LecturerSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Lecturer
        fields = ['user', 'University', 'Department']

    def create(self, validated_data):
        user_data = validated_data.pop('user')  # Extract user data
        user = User.objects.create_user(**user_data)  # Create User instance
        lecturer = Lecturer.objects.create(user=user, **validated_data)  # Create Lecturer instance
        return lecturer


# StudentSerializer (handles creation of Student with linked User)
class StudentSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Student
        fields = ['user', 'student_name', 'student_email', 'roll_number']

    def create(self, validated_data):
        user_data = validated_data.pop('user')  # Extract user data
        user = User.objects.create_user(**user_data)  # Create User instance
        student = Student.objects.create(user=user, **validated_data)  # Create Student instance
        return student


# Serializer for the Module model
class ModuleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Module
        fields = ['id', 'name', 'code', 'description', 'lecturer']
        extra_kwargs = {
            'lecturer': {'read_only': True},
        }


class AssignmentSerializer(serializers.ModelSerializer):
    module_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Assignment
        fields = ['id', 'title', 'description', 'due_date', 'module', 'module_id']
        extra_kwargs = {
            'module': {'read_only': True},
            'module_id': {'write_only': True},
        }


# Serializer for the Submission model

class FileUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Submission
        fields = ['id', 'assignment', 'file', 'uploaded_at']
        extra_kwargs = {
            'assignment': {'write_only': True},
        }

class ScoreUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Submission
        fields = ['id', 'score']
