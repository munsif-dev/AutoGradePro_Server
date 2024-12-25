from rest_framework import serializers
from django.contrib.auth.models import User  # Import Django's built-in User model
from .models import Lecturer
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Lecturer, Student, Module, Assignment, Submission, MarkingScheme, Answer


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
        fields = ['id', 'name', 'code', 'description', 'lecturer', 'created_at']
        extra_kwargs = {
            'lecturer': {'read_only': True},
            'created_at': {'read_only' : True}
        }


class AssignmentSerializer(serializers.ModelSerializer):
    module_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Assignment
        fields = ['id', 'title', 'description', 'due_date', 'module', 'module_id']
        extra_kwargs = {
            'module': {'read_only': True},
            'module_id': {'write_only': True},
            'created_at': {'read_only' : True}
        }

class AssignmentPageSerializer(serializers.ModelSerializer):
    module = ModuleSerializer()  # Nesting the ModuleSerializer here

    class Meta:
        model = Assignment
        fields = ['id', 'title', 'description', 'due_date', 'module']


# Serializer for the Submission model
class FileUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Submission
        fields = ['id', 'assignment', 'file', 'file_name', 'uploaded_at']
        extra_kwargs = {
            'assignment': {'write_only': True},
            'file_name': {'read_only': True},  # Optional: Ensure the file name is not editable via API
        }

class ScoreUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Submission
        fields = ['id', 'score']


# Serializer for the Answer model
class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ['id', 'answer_text', 'marks']
        
class MarkingSchemeSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True)

    class Meta:
        model = MarkingScheme
        fields = ['id', 'assignment', 'title', 'answers', 'created_at', 'updated_at']
        read_only_fields = ['title', 'created_at', 'updated_at']

    def create(self, validated_data):
        answers_data = validated_data.pop('answers', [])
        assignment = validated_data.get('assignment')

        # Dynamically fetch title from the assignment
        validated_data['title'] = assignment.title

        # Create the marking scheme
        marking_scheme = MarkingScheme.objects.create(**validated_data)

        # Assign marking_scheme to each answer and create them
        for answer_data in answers_data:
            Answer.objects.create(marking_scheme=marking_scheme, **answer_data)

        return marking_scheme
    
    def update(self, instance, validated_data):
        answers_data = validated_data.pop('answers', [])
        instance.title = validated_data.get('title', instance.title)
        instance.save()

        # Remove all existing answers first
        Answer.objects.filter(marking_scheme=instance).delete()

        # Create new answers with auto-generated IDs starting from 1
        for answer_data in answers_data:
            # Remove the 'id' field to allow the database to assign a new auto-incremented ID
            answer_data.pop('id', None)  # Ensure 'id' is removed
            Answer.objects.create(
                marking_scheme=instance,
                answer_text=answer_data.get('answer_text'),
                marks=answer_data.get('marks')
            )

        return instance
