# Generated by Django 4.2 on 2023-08-14 09:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_remove_sample_comment_discretesamplevalue_comment_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='action',
            name='sounding',
            field=models.IntegerField(blank=True, null=True, verbose_name='Sounding'),
        ),
    ]
