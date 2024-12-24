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
        fields = ['id', 'assignment', 'file', 'file_name', 'uploaded_at']
        extra_kwargs = {
            'assignment': {'write_only': True},
            'file_name': {'read_only': True},  # Optional: Ensure the file name is not editable via API
        }

class ScoreUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Submission
        fields = ['id', 'score']


# Serializer for the MarkingScheme model

class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ["id", "answer_text", "marks"]

class MarkingSchemeSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True, write_only=True)

    class Meta:
        model = MarkingScheme
        fields = ["id", "title", "created_at", "updated_at", "answers"]
        read_only_fields = ["created_at", "updated_at"]

    def create(self, validated_data):
        # Extract answers from validated data
        answers_data = validated_data.pop("answers")
        # Create the marking scheme instance
        marking_scheme = MarkingScheme.objects.create(**validated_data)
        # Create associated answers
        for answer_data in answers_data:
            Answer.objects.create(marking_scheme=marking_scheme, **answer_data)
        return marking_scheme

    def update(self, instance, validated_data):
        # Extract answers from validated data
        answers_data = validated_data.pop("answers", [])
        # Update marking scheme fields
        instance.title = validated_data.get("title", instance.title)
        instance.save()
        # Update answers
        existing_answers = {answer.id: answer for answer in instance.answers.all()}
        for answer_data in answers_data:
            answer_id = answer_data.get("id")
            if answer_id and answer_id in existing_answers:
                # Update existing answer
                answer = existing_answers.pop(answer_id)
                answer.answer_text = answer_data.get("answer_text", answer.answer_text)
                answer.marks = answer_data.get("marks", answer.marks)
                answer.save()
            else:
                # Create new answer
                Answer.objects.create(marking_scheme=instance, **answer_data)
        # Delete remaining answers that were not included in the update
        for answer in existing_answers.values():
            answer.delete()
        return instance