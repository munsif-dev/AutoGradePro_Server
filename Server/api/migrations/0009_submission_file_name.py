# Generated by Django 5.1.2 on 2024-12-23 12:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0008_submission_file_hash'),
    ]

    operations = [
        migrations.AddField(
            model_name='submission',
            name='file_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]