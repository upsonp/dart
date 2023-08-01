# Generated by Django 4.2 on 2023-07-29 16:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_event'),
    ]

    operations = [
        migrations.CreateModel(
            name='Instrument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='Instrument')),
                ('type', models.IntegerField(choices=[(1, 'CTD'), (2, 'Net'), (3, 'Mooring'), (4, 'Buoy'), (5, 'VPR'), (999, 'Other')], default=999, verbose_name='Instrument type')),
            ],
        ),
        migrations.AddField(
            model_name='event',
            name='station',
            field=models.CharField(default='NA_01', max_length=20, verbose_name='Station'),
            preserve_default=False,
        ),
        migrations.CreateModel(
            name='DataFileDirectory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('directory', models.FileField(help_text='Absolute Path to Directory', upload_to='', verbose_name='Directory')),
                ('file_type', models.IntegerField(choices=[(1, '.LOG'), (2, '.BTL'), (3, '.ROS')], verbose_name='File Types')),
                ('mission', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='files', to='core.mission', verbose_name='Mission')),
            ],
        ),
        migrations.AddField(
            model_name='event',
            name='instrument',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.DO_NOTHING, related_name='events', to='core.instrument', verbose_name='Instrument'),
            preserve_default=False,
        ),
    ]
