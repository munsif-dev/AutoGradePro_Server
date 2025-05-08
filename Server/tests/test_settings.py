from django.test import TestCase
from django.conf import settings

class SettingsTestCase(TestCase):
    def test_installed_apps(self):
        """Test that all required apps are installed"""
        self.assertIn('api.apps.ApiConfig', settings.INSTALLED_APPS)
        self.assertIn('rest_framework', settings.INSTALLED_APPS)
        self.assertIn('corsheaders', settings.INSTALLED_APPS)

    def test_rest_framework_settings(self):
        """Test REST framework settings"""
        self.assertIn('rest_framework_simplejwt.authentication.JWTAuthentication', 
                     settings.REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'])
        self.assertIn('rest_framework.permissions.IsAuthenticated', 
                     settings.REST_FRAMEWORK['DEFAULT_PERMISSION_CLASSES'])