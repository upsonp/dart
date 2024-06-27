# Generated by Django 4.2 on 2024-06-27 12:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('settingsdb', '0008_sampletypeconfig_limit_field'),
    ]

    operations = [
        migrations.AddField(
            model_name='bcdatabaseconnection',
            name='bc_discrete_data_edits',
            field=models.CharField(default='BCDISCRETEDATAEDITS', max_length=60, verbose_name='BCD Table Name'),
        ),
        migrations.AddField(
            model_name='bcdatabaseconnection',
            name='bc_discrete_station_edits',
            field=models.CharField(default='BCDISCRETESTATNEDITS', max_length=60, verbose_name='BCD Table Name'),
        ),
        migrations.AddField(
            model_name='bcdatabaseconnection',
            name='bc_plankton_data_edits',
            field=models.CharField(default='BCPLANKTONDATAEDITS', max_length=60, verbose_name='BCD Table Name'),
        ),
        migrations.AddField(
            model_name='bcdatabaseconnection',
            name='bc_plankton_station_edits',
            field=models.CharField(default='BCPLANKTONSTATNEDITS', max_length=60, verbose_name='BCD Table Name'),
        ),
    ]