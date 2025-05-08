from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIRequestFactory
from api.models import Lecturer, Module, Assignment, MarkingScheme, Answer
from api.serializers import (
    UserSerializer, LecturerSerializer, ModuleSerializer, 
    AssignmentSerializer, MarkingSchemeSerializer
)
from django.utils import timezone
from datetime import timedelta

class UserSerializerTest(TestCase):
    def setUp(self):
        self.user_attributes = {
            'username': 'testuser',
            'password': 'testpassword',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }

    def test_user_serializer_create(self):
        """Test UserSerializer create method"""
        serializer = UserSerializer(data=self.user_attributes)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.first_name, 'Test')
        self.assertEqual(user.last_name, 'User')
        # Verify password is hashed
        self.assertTrue(user.check_password('testpassword'))

class LecturerSerializerTest(TestCase):
    def setUp(self):
        self.lecturer_attributes = {
            'user': {
                'username': 'testlecturer',
                'password': 'testpassword',
                'email': 'lecturer@example.com',
                'first_name': 'Test',
                'last_name': 'Lecturer'
            },
            'university': 'Test University',
            'department': 'Computer Science'
        }

    def test_lecturer_serializer_create(self):
        """Test LecturerSerializer create method"""
        serializer = LecturerSerializer(data=self.lecturer_attributes)
        self.assertTrue(serializer.is_valid())
        lecturer = serializer.save()
        
        # Verify lecturer fields
        self.assertEqual(lecturer.university, 'Test University')
        self.assertEqual(lecturer.department, 'Computer Science')
        
        # Verify user fields
        self.assertEqual(lecturer.user.username, 'testlecturer')
        self.assertEqual(lecturer.user.email, 'lecturer@example.com')
        self.assertTrue(lecturer.user.check_password('testpassword'))

class ModuleSerializerTest(TestCase):
    def setUp(self):
        # Create a lecturer
        self.user = User.objects.create_user(username='testlecturer', password='testpassword')
        self.lecturer = Lecturer.objects.create(user=self.user, university='Test University')
        
        # Module data
        self.module_data = {
            'name': 'Test Module',
            'code': 'TM101',
            'description': 'A test module'
        }
    
    def test_module_serializer(self):
        """Test ModuleSerializer"""
        serializer = ModuleSerializer(data=self.module_data)
        self.assertTrue(serializer.is_valid())

class MarkingSchemeSerializerTest(TestCase):
    def setUp(self):
        # Create test objects
        self.user = User.objects.create_user(username='testlecturer', password='testpassword')
        self.lecturer = Lecturer.objects.create(user=self.user)
        self.module = Module.objects.create(name='Test Module', code='TM101', lecturer=self.lecturer)
        self.assignment = Assignment.objects.create(
            title='Test Assignment',
            due_date=timezone.now() + timedelta(days=7),
            module=self.module
        )
        
        # Marking scheme data
        self.marking_scheme_data = {
            'assignment': self.assignment.id,
            'pass_score': 50,
            'answers': [
                {
                    'question_text': 'What is 2+2?',
                    'answer_text': '4',
                    'marks': 10,
                    'grading_type': 'numerical'
                },
                {
                    'question_text': 'List three primary colors',
                    'answer_text': 'Red, Blue, Yellow',
                    'marks': 15,
                    'grading_type': 'list',
                    'partial_matching': True
                }
            ]
        }

    def test_marking_scheme_serializer_create(self):
        """Test MarkingSchemeSerializer create method"""
        serializer = MarkingSchemeSerializer(data=self.marking_scheme_data)
        self.assertTrue(serializer.is_valid())
        marking_scheme = serializer.save()
        
        # Verify marking scheme fields
        self.assertEqual(marking_scheme.assignment, self.assignment)
        self.assertEqual(marking_scheme.pass_score, 50)
        self.assertEqual(marking_scheme.title, self.assignment.title)  # Auto-generated title
        
        # Verify answers
        self.assertEqual(marking_scheme.answers.count(), 2)
        
        answers = marking_scheme.answers.all()
        self.assertEqual(answers[0].question_text, 'What is 2+2?')
        self.assertEqual(answers[0].grading_type, 'numerical')
        
        self.assertEqual(answers[1].question_text, 'List three primary colors')
        self.assertEqual(answers[1].grading_type, 'list')
        self.assertTrue(answers[1].partial_matching)