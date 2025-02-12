from django.contrib import admin
from .models import User, Lecturer

admin.site.register(Lecturer)
# Compare this snippet from Server/api/urls.py: