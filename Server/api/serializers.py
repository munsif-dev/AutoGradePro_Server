from rest_framework import serializers
from django.contrib.auth.models import User  # Import Django's built-in User model
from .models import Lecturer
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Lecturer, Student, Module, Assignment, Submission, MarkingScheme, Answer, GradingResult


# UserSerializer (handles user creation and updating)
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'email', 'first_name', 'last_name']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)

        # Update all remaining fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)  # Proper password hashing

        instance.save()
        return instance


# LecturerSerializer (handles creation of Lecturer with linked User)
class LecturerSerializer(serializers.ModelSerializer):
    user = UserSerializer()  # Nested user serializer for related user fields
   
    class Meta:
        model = Lecturer
        fields = ['user', 'university', 'department']

    def create(self, validated_data):
        user_data = validated_data.pop('user')  # Extract user data
        user = User.objects.create_user(**user_data)  # Create User instance
        lecturer = Lecturer.objects.create(user=user, **validated_data)  # Create Lecturer instance
        return lecturer

class LecturerDetailSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Lecturer
        fields = ['user', 'university', 'department', 'profile_picture']

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', None)
        print(user_data)
        if user_data:
            user_serializer = UserSerializer(
                instance=instance.user,
                data=user_data,
                partial=True,
                context=self.context  # Pass context for request.user, etc.
            )
            user_serializer.is_valid(raise_exception=True)
            user_serializer.save()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
        

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

# New serializer for fetching file list with scores
class FileListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Submission
        fields = ['id', 'assignment', 'file', 'file_name', 'uploaded_at', 'score']


# Serializer for the Answer model
class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = [  'id',
            'answer_text',
            'marks',
            'grading_type',
            'case_sensitive',
            'order_sensitive',
            'range_sensitive',
            'range',]



class GradingResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = GradingResult
        fields = [
            'id', 
            'question_id', 
            'student_answer', 
            'correct_answer', 
            'marks_awarded', 
            'allocated_marks',
            'grading_type',
            'is_correct'
        ]
        
        
class MarkingSchemeSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True)

    class Meta:
        model = MarkingScheme
        fields = ['id', 'assignment', 'title','pass_score', 'answers', 'created_at', 'updated_at']
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
        instance.pass_score = validated_data.get('pass_score', instance.pass_score)
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
                grading_type=answer_data.get('grading_type'),
                case_sensitive=answer_data.get('case_sensitive'),
                order_sensitive=answer_data.get('order_sensitive'),
                range_sensitive=answer_data.get('range_sensitive'),
                range=answer_data.get('range') or {},
                marks=answer_data.get('marks')
            )

        return instance
