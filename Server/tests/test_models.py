from django.test import TestCase
from django.contrib.auth.models import User
from api.models import (
    Lecturer, Student, Module, Assignment, 
    Submission, MarkingScheme, Answer, GradingResult
)
from django.utils import timezone
from datetime import timedelta

class LecturerModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testlecturer',
            password='testpassword',
            email='test@example.com'
        )
        self.lecturer = Lecturer.objects.create(
            user=self.user,
            university='Test University',
            department='Computer Science'
        )

    def test_string_representation(self):
        """Test the string representation of Lecturer"""
        self.assertEqual(str(self.lecturer), self.user.username)

    def test_lecturer_fields(self):
        """Test Lecturer model fields"""
        self.assertEqual(self.lecturer.university, 'Test University')
        self.assertEqual(self.lecturer.department, 'Computer Science')
        self.assertEqual(self.lecturer.user, self.user)

class ModuleModelTest(TestCase):
    def setUp(self):
        # Create test user and lecturer
        self.user = User.objects.create_user(
            username='testlecturer',
            password='testpassword'
        )
        self.lecturer = Lecturer.objects.create(
            user=self.user,
            university='Test University'
        )
        
        # Create test module
        self.module = Module.objects.create(
            name='Test Module',
            code='TM101',
            description='A test module',
            lecturer=self.lecturer
        )

    def test_module_creation(self):
        """Test Module creation"""
        self.assertEqual(self.module.name, 'Test Module')
        self.assertEqual(self.module.code, 'TM101')
        self.assertEqual(self.module.lecturer, self.lecturer)
    
    def test_string_representation(self):
        """Test the string representation of Module"""
        self.assertEqual(str(self.module), 'Test Module (TM101)')

class AssignmentModelTest(TestCase):
    def setUp(self):
        # Create test user and lecturer
        self.user = User.objects.create_user(
            username='testlecturer',
            password='testpassword'
        )
        self.lecturer = Lecturer.objects.create(
            user=self.user
        )
        
        # Create test module
        self.module = Module.objects.create(
            name='Test Module',
            code='TM101',
            lecturer=self.lecturer
        )
        
        # Create test assignment
        self.due_date = timezone.now() + timedelta(days=7)
        self.assignment = Assignment.objects.create(
            title='Test Assignment',
            description='A test assignment',
            due_date=self.due_date,
            module=self.module
        )

    def test_assignment_creation(self):
        """Test Assignment creation"""
        self.assertEqual(self.assignment.title, 'Test Assignment')
        self.assertEqual(self.assignment.module, self.module)
        self.assertEqual(self.assignment.due_date, self.due_date)
    
    def test_string_representation(self):
        """Test the string representation of Assignment"""
        self.assertEqual(str(self.assignment), 'Test Assignment - Test Module')

class MarkingSchemeModelTest(TestCase):
    def setUp(self):
        # Create test user, lecturer, module, and assignment
        self.user = User.objects.create_user(username='testlecturer', password='testpassword')
        self.lecturer = Lecturer.objects.create(user=self.user)
        self.module = Module.objects.create(name='Test Module', code='TM101', lecturer=self.lecturer)
        self.assignment = Assignment.objects.create(
            title='Test Assignment',
            due_date=timezone.now() + timedelta(days=7),
            module=self.module
        )
        
        # Create marking scheme
        self.marking_scheme = MarkingScheme.objects.create(
            assignment=self.assignment,
            title='Test Marking Scheme',
            pass_score=50
        )
        
        # Create test answers
        self.answer1 = Answer.objects.create(
            marking_scheme=self.marking_scheme,
            question_text='What is 2+2?',
            answer_text='4',
            marks=10,
            grading_type='numerical'
        )
        
        self.answer2 = Answer.objects.create(
            marking_scheme=self.marking_scheme,
            question_text='List three primary colors',
            answer_text='Red, Blue, Yellow',
            marks=15,
            grading_type='list',
            partial_matching=True
        )

    def test_marking_scheme_creation(self):
        """Test MarkingScheme creation"""
        self.assertEqual(self.marking_scheme.title, 'Test Marking Scheme')
        self.assertEqual(self.marking_scheme.assignment, self.assignment)
        self.assertEqual(self.marking_scheme.pass_score, 50)
    
    def test_answer_creation(self):
        """Test Answer creation"""
        self.assertEqual(self.answer1.question_text, 'What is 2+2?')
        self.assertEqual(self.answer1.answer_text, '4')
        self.assertEqual(self.answer1.grading_type, 'numerical')
        
        self.assertEqual(self.answer2.question_text, 'List three primary colors')
        self.assertEqual(self.answer2.answer_text, 'Red, Blue, Yellow')
        self.assertEqual(self.answer2.grading_type, 'list')
        self.assertTrue(self.answer2.partial_matching)