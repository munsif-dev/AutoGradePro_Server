"""
URL configuration for Server project.

The urlpatterns list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# In urls.py of your Django app
from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from api.views import CreateLecturerView, CreateStudentView  # Import your new views
from django.conf import settings
from django.conf.urls.static import static
from whitenoise.middleware import WhiteNoiseMiddleware

urlpatterns = [
    # Admin route
    path("admin/", admin.site.urls),

    ## why do we need to include the following routes?
    # Include the JWT Token Authentication routes to get and refresh tokens
    # If this is not included, the JWT Token Authentication will not work
    # it is good to include these routes in the main urls.py file

    # JWT Token Authentication routes
    path("api/token/", TokenObtainPairView.as_view(), name="get_token"),  # Obtain JWT Token
    path("api/token/refresh/", TokenRefreshView.as_view(), name="refresh"),  # Refresh JWT Token

    # Custom API routes for creating Lecturer and Student
    path("api/lecturer/register/", CreateLecturerView.as_view(), name="create-lecturer"),  # Create Lecturer
    path("api/student/register/", CreateStudentView.as_view(), name="create-student"),  # Create Student

    # API Auth routes
    path("api-auth/", include("rest_framework.urls")),

    # Include app-specific URLs , these are used to create delete, update and retrieve modules assignments, submissions
    path("api/", include("api.urls")),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



# Create a custom WhiteNoise instance for media files
whitenoise_middleware = WhiteNoiseMiddleware()
whitenoise_middleware.add_files(settings.MEDIA_ROOT, prefix=settings.MEDIA_URL)

# Add a pattern for media files
if settings.DEBUG:
    # Django's default media serving for development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # WhiteNoise media serving for production
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', whitenoise_middleware.serve, {'root': settings.MEDIA_ROOT}),
    ]