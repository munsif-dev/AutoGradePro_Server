from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from api.models import (
    Lecturer, Module, Assignment, Submission, 
    MarkingScheme, Answer, GradingResult
)
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django.core.files.uploadedfile import SimpleUploadedFile
import tempfile
import os
from django.conf import settings
import json

class GradingIntegrationTest(TestCase):
    def setUp(self):
        # Create user and authenticate
        self.user = User.objects.create_user(
            username='testlecturer',
            password='testpassword'
        )
        self.lecturer = Lecturer.objects.create(
            user=self.user,
            university='Test University'
        )
        
        # Create module, assignment, and marking scheme
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
        
        # Create marking scheme with answers
        self.marking_scheme = MarkingScheme.objects.create(
            assignment=self.assignment,
            title='Test Marking Scheme',
            pass_score=50
        )
        
        # Create different types of answers for testing different grading types
        self.answers = [
            Answer.objects.create(
                marking_scheme=self.marking_scheme,
                question_text='What is the capital of France?',
                answer_text='Paris',
                marks=10,
                grading_type='one-word',
                case_sensitive=True
            ),
            Answer.objects.create(
                marking_scheme=self.marking_scheme,
                question_text='What is 2+2?',
                answer_text='4',
                marks=5,
                grading_type='numerical'
            ),
            Answer.objects.create(
                marking_scheme=self.marking_scheme,
                question_text='List three primary colors.',
                answer_text='Red, Blue, Yellow',
                marks=15,
                grading_type='list',
                partial_matching=True
            )
        ]
        
        # Create a submission file
        self.submission_content = (
            "1. Paris\n"
            "2. 4\n"
            "3. Red, Blue, Yellow\n"
        )
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt', mode='w+') as temp:
            temp.write(self.submission_content)
            temp.flush()
            temp.seek(0)
            self.temp_file_path = temp.name
        
        # Create submission record
        with open(self.temp_file_path, 'rb') as f:
            file_content = f.read()
            
        self.submission_file = SimpleUploadedFile('answers.txt', file_content)
        self.submission = Submission.objects.create(
            assignment=self.assignment,
            file=self.submission_file
        )
        
        # Authenticate client
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def tearDown(self):
        # Clean up temporary files
        try:
            if hasattr(self, 'temp_file_path') and os.path.exists(self.temp_file_path):
                os.unlink(self.temp_file_path)
            
            # Clean up media files
            if hasattr(self, 'submission') and self.submission.file:
                if os.path.exists(self.submission.file.path):
                    os.unlink(self.submission.file.path)
        except Exception as e:
            print(f"Error during tearDown: {e}")
    
    def test_grading_workflow(self):
        """Test the complete grading workflow"""
        # Step 1: Grade the submission
        grade_url = reverse('grade-submission', args=[self.assignment.id])
        grade_response = self.client.put(grade_url)
        self.assertEqual(grade_response.status_code, 200)
        
        # Verify submission is graded
        self.submission.refresh_from_db()
        self.assertIsNotNone(self.submission.score)
        
        # Step 2: Get grading results
        results_url = reverse('grading-results-list', args=[self.submission.id])
        results_response = self.client.get(results_url)
        self.assertEqual(results_response.status_code, 200)
        
        # Verify correct number of grading results
        self.assertEqual(len(results_response.data), 3)
        
        # Step 3: Check file detail view
        detail_url = reverse('submission_report', args=[self.assignment.id, self.submission.id])
        detail_response = self.client.get(detail_url)
        self.assertEqual(detail_response.status_code, 200)
        
        # Verify response contains correct data
        self.assertIn('file', detail_response.data)
        self.assertIn('answers', detail_response.data)
        self.assertIn('marking_scheme', detail_response.data)
        self.assertIn('score', detail_response.data)
        
        # Step 4: Test clear grading results
        clear_url = reverse('clear-grading-results', args=[self.assignment.id])
        clear_response = self.client.delete(clear_url)
        self.assertEqual(clear_response.status_code, 200)
        
        # Verify grading results are cleared
        self.assertEqual(GradingResult.objects.filter(submission=self.submission).count(), 0)
        
        # Verify submission score is reset
        self.submission.refresh_from_db()
        self.assertIsNone(self.submission.score)