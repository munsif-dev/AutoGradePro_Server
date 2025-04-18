# Generated by Django 5.1.3 on 2025-04-07 03:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0023_gradingresult'),
    ]

    operations = [
        migrations.AddField(
            model_name='answer',
            name='partial_matching',
            field=models.BooleanField(default=False, help_text='For list type answers, allow partial credit for partially correct lists'),
        ),
        migrations.AddField(
            model_name='answer',
            name='question_text',
            field=models.TextField(blank=True, help_text='The text of the question', null=True),
        ),
        migrations.AddField(
            model_name='answer',
            name='semantic_threshold',
            field=models.FloatField(default=0.7, help_text='Threshold for semantic matching (0-1) for short-phrase answers'),
        ),
        migrations.AlterField(
            model_name='answer',
            name='range',
            field=models.JSONField(blank=True, default=dict, help_text="Range for numerical answers, e.g., {'min': 0, 'max': 100, 'tolerance_percent': 5}", null=True),
        ),
    ]
