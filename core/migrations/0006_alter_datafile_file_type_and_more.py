# Generated by Django 4.1.3 on 2022-12-22 13:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_hplcsample'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datafile',
            name='file_type',
            field=models.IntegerField(choices=[(1, '.LOG'), (2, '.BTL'), (3, '.ROS')], verbose_name='File Type'),
        ),
        migrations.AlterField(
            model_name='datafiledirectorytype',
            name='file_type',
            field=models.IntegerField(choices=[(1, '.LOG'), (2, '.BTL'), (3, '.ROS')], verbose_name='File Types'),
        ),
        migrations.AlterField(
            model_name='hplcsample',
            name='chla',
            field=models.FloatField(blank=True, null=True, verbose_name='HPLCHLA'),
        ),
        migrations.AlterField(
            model_name='hplcsample',
            name='phaeo',
            field=models.FloatField(blank=True, null=True, verbose_name='HPLCPHAE'),
        ),
    ]
