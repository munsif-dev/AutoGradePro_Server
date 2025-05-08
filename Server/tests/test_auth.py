from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from api.models import Lecturer
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

class AuthenticationTest(TestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword',
            email='test@example.com'
        )
        self.lecturer = Lecturer.objects.create(
            user=self.user,
            university='Test University',
            department='Computer Science'
        )
        
        # Create client
        self.client = APIClient()
    
    def test_token_obtain(self):
        """Test obtaining JWT token"""
        url = reverse('get_token')
        response = self.client.post(url, {
            'username': 'testuser',
            'password': 'testpassword'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
    
    def test_token_refresh(self):
        """Test refreshing JWT token"""
        # First get a token
        refresh = RefreshToken.for_user(self.user)
        
        # Then try to refresh it
        url = reverse('refresh')
        response = self.client.post(url, {
            'refresh': str(refresh)
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
    
    def test_authenticated_endpoint(self):
        """Test accessing an authenticated endpoint"""
        # Try without authentication
        url = reverse('module-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Try with authentication
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_lecturer_registration(self):
        """Test lecturer registration endpoint"""
        url = reverse('create-lecturer')
        data = {
            'user': {
                'username': 'newlecturer',
                'password': 'newpassword',
                'email': 'new@example.com',
                'first_name': 'New',
                'last_name': 'Lecturer'
            },
            'university': 'New University',
            'department': 'Physics'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Lecturer.objects.count(), 2)
        self.assertEqual(User.objects.count(), 2)
        
        # Verify the user was created correctly
        new_user = User.objects.get(username='newlecturer')
        self.assertEqual(new_user.email, 'new@example.com')
        self.assertEqual(new_user.first_name, 'New')
        self.assertEqual(new_user.last_name, 'Lecturer')
        
        # Verify the lecturer was created correctly
        new_lecturer = Lecturer.objects.get(user=new_user)
        self.assertEqual(new_lecturer.university, 'New University')
        self.assertEqual(new_lecturer.department, 'Physics')
    
    def test_password_change(self):
        """Test password change endpoint"""
        # Authenticate
        self.client.force_authenticate(user=self.user)
        
        # Change password
        url = reverse('password-change')
        data = {
            'current_password': 'testpassword',
            'new_password': 'newpassword',
            'confirm_password': 'newpassword'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify password was changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpassword'))