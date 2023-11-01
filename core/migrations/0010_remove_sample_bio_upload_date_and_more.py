# Generated by Django 4.2 on 2023-10-24 15:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_missionsampletype'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sample',
            name='bio_upload_date',
        ),
        migrations.AddField(
            model_name='discretesamplevalue',
            name='bio_upload_date',
            field=models.DateTimeField(blank=True, help_text='Date of last BioChem upload', null=True, verbose_name='BioChem Uploaded'),
        ),
    ]
