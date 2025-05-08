from django.test import TestCase
from rest_framework.test import APIClient, APITestCase
from django.contrib.auth.models import User
from api.models import (
    Lecturer, Module, Assignment, Submission, 
    MarkingScheme, Answer, GradingResult
)
from django.urls import reverse
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
import tempfile
from PIL import Image
import io
import json
import os

class ModuleViewsTest(APITestCase):
    def setUp(self):
        # Create test user and authenticate
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
        
        # Create a test module
        self.module = Module.objects.create(
            name='Test Module',
            code='TM101',
            description='A test module',
            lecturer=self.lecturer
        )
        
        # Authenticate
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_module_list_create(self):
        """Test module list and create endpoints"""
        # Test listing modules
        url = reverse('module-list-create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        # Test creating a module
        module_data = {
            'name': 'New Module',
            'code': 'NM102',
            'description': 'A new module'
        }
        response = self.client.post(url, module_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Module.objects.count(), 2)
        self.assertEqual(Module.objects.filter(name='New Module').count(), 1)
    
    def test_module_detail(self):
        """Test module detail endpoint"""
        url = reverse('module-detail', args=[self.module.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Module')
    
    def test_module_update(self):
        """Test module update endpoint"""
        url = reverse('module-edit', args=[self.module.id])
        update_data = {
            'name': 'Updated Module',
            'code': 'UM101',
            'description': 'An updated module'
        }
        response = self.client.put(url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Refresh from db
        self.module.refresh_from_db()
        self.assertEqual(self.module.name, 'Updated Module')
        self.assertEqual(self.module.code, 'UM101')
    
    def test_module_delete(self):
        """Test module delete endpoint"""
        url = reverse('module-delete', args=[self.module.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Module.objects.count(), 0)

class AssignmentViewsTest(APITestCase):
    def setUp(self):
        # Create test user and authenticate
        self.user = User.objects.create_user(
            username='testlecturer',
            password='testpassword'
        )
        self.lecturer = Lecturer.objects.create(
            user=self.user,
            university='Test University'
        )
        
        # Create a test module
        self.module = Module.objects.create(
            name='Test Module',
            code='TM101',
            lecturer=self.lecturer
        )
        
        # Create a test assignment
        self.due_date = timezone.now() + timedelta(days=7)
        self.assignment = Assignment.objects.create(
            title='Test Assignment',
            description='A test assignment',
            due_date=self.due_date,
            module=self.module
        )
        
        # Authenticate
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_assignment_list_create(self):
        """Test assignment list and create endpoints"""
        # Test listing assignments
        url = reverse('assignment-list-create') + f'?module_id={self.module.id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        # Test creating an assignment
        assignment_data = {
            'title': 'New Assignment',
            'description': 'A new assignment',
            'due_date': (timezone.now() + timedelta(days=14)).isoformat(),
            'module_id': self.module.id
        }
        response = self.client.post(reverse('assignment-list-create'), assignment_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Assignment.objects.count(), 2)
    
    def test_assignment_detail(self):
        """Test assignment detail endpoint"""
        url = reverse('assignment-list', args=[self.assignment.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Assignment')
    
    def test_assignment_update(self):
        """Test assignment update endpoint"""
        url = reverse('assignment-edit', args=[self.assignment.id])
        update_data = {
            'title': 'Updated Assignment',
            'description': 'An updated assignment',
            'due_date': (timezone.now() + timedelta(days=10)).isoformat(),
            'module_id': self.module.id
        }
        response = self.client.put(url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Refresh from db
        self.assignment.refresh_from_db()
        self.assertEqual(self.assignment.title, 'Updated Assignment')
    
    def test_assignment_delete(self):
        """Test assignment delete endpoint"""
        url = reverse('assignment-delete', args=[self.assignment.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Assignment.objects.count(), 0)

class MarkingSchemeViewsTest(APITestCase):
    def setUp(self):
        # Create test user and authenticate
        self.user = User.objects.create_user(
            username='testlecturer',
            password='testpassword'
        )
        self.lecturer = Lecturer.objects.create(
            user=self.user
        )
        
        # Create module and assignment
        self.module = Module.objects.create(
            name='Test Module',
            code='TM101',
            lecturer=self.lecturer
        )
        self.assignment = Assignment.objects.create(
            title='Test Assignment',
            due_date=timezone.now() + timedelta(days=7),
            module=self.module
        )
        
        # Authenticate
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_marking_scheme_create(self):
        """Test marking scheme creation endpoint"""
        url = reverse('marking-scheme-create', args=[self.assignment.id])
        marking_scheme_data = {
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
        response = self.client.post(url, marking_scheme_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify marking scheme created
        self.assertEqual(MarkingScheme.objects.count(), 1)
        self.assertEqual(Answer.objects.count(), 2)
    
    def test_marking_scheme_retrieve(self):
        """Test marking scheme retrieve endpoint"""
        # First create a marking scheme
        marking_scheme = MarkingScheme.objects.create(
            assignment=self.assignment,
            title='Test Marking Scheme',
            pass_score=50
        )
        Answer.objects.create(
            marking_scheme=marking_scheme,
            question_text='What is 2+2?',
            answer_text='4',
            marks=10,
            grading_type='numerical'
        )
        
        url = reverse('marking-scheme-detail', args=[self.assignment.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Marking Scheme')
        self.assertEqual(len(response.data['answers']), 1)
    
    def test_marking_scheme_update(self):
        """Test marking scheme update endpoint"""
        # First create a marking scheme
        marking_scheme = MarkingScheme.objects.create(
            assignment=self.assignment,
            title='Test Marking Scheme',
            pass_score=50
        )
        Answer.objects.create(
            marking_scheme=marking_scheme,
            question_text='What is 2+2?',
            answer_text='4',
            marks=10,
            grading_type='numerical'
        )
        
        # Update with new data
        url = reverse('marking-scheme-detail', args=[self.assignment.id])
        update_data = {
            'pass_score': 60,
            'answers': [
                {
                    'id': 1,  # This ID will be ignored as per your serializer implementation
                    'question_text': 'What is 3+3?',
                    'answer_text': '6',
                    'marks': 15,
                    'grading_type': 'numerical'
                },
                {
                    'question_text': 'New question',
                    'answer_text': 'New answer',
                    'marks': 20,
                    'grading_type': 'one-word'
                }
            ]
        }
        response = self.client.put(url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify updates
        marking_scheme.refresh_from_db()
        self.assertEqual(marking_scheme.pass_score, 60)
        self.assertEqual(Answer.objects.count(), 2)  # Old answer replaced with two new ones