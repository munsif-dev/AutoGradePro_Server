# Generated by Django 5.1.3 on 2025-03-20 15:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0017_rename_department_lecturer_department_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='lecturer',
            name='profile_picture',
        ),
    ]
