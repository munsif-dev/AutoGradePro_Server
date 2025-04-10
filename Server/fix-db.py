#!/usr/bin/env python
"""
This script updates the database settings in settings.py to use hardcoded values.
"""
import re

# Path to the settings file
settings_file = 'Server/settings.py'

# Read the current settings
with open(settings_file, 'r') as f:
    content = f.read()

# Define the new database settings block
db_settings = """
# Database configuration - hardcoded for Docker deployment
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'autogradepro',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': 'db',
        'PORT': '5432',
    }
}
"""

# Look for existing DATABASES definition
if 'DATABASES = {' in content:
    # Replace the existing DATABASES block
    pattern = r"DATABASES\s*=\s*\{[^}]*\}"
    content = re.sub(pattern, db_settings.strip(), content, flags=re.DOTALL)
else:
    # Append to the end of the file
    content += "\n" + db_settings

# Write the updated content back
with open(settings_file, 'w') as f:
    f.write(content)

print(f"Updated {settings_file} with hardcoded database settings")