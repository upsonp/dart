# Generated by Django 4.2 on 2023-08-01 17:00

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_remove_error_file_name_fileerror'),
    ]

    operations = [
        migrations.AlterField(
            model_name='instrument',
            name='type',
            field=models.IntegerField(choices=[(1, 'CTD'), (2, 'Net'), (3, 'Mooring'), (4, 'Buoy'), (5, 'VPR'), (999, 'Other')], default=999, verbose_name='Instrument Type'),
        ),
        migrations.CreateModel(
            name='Action',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_time', models.DateTimeField(verbose_name='Date/Time')),
                ('latitude', models.FloatField(verbose_name='Latitude')),
                ('longitude', models.FloatField(verbose_name='Longitude')),
                ('file', models.CharField(blank=True, max_length=100, null=True, verbose_name='File Name')),
                ('mid', models.IntegerField(blank=True, null=True, verbose_name='$@MID@$')),
                ('type', models.IntegerField(choices=[(1, 'Deployed'), (2, 'Bottom'), (3, 'Recovered'), (4, 'Aborted'), (5, 'Attempted Comms'), (6, 'Release'), (7, 'On Deck'), (8, 'In Water'), (9, 'Start Deployment'), (10, 'On Bottom'), (11, 'Started'), (999, 'Other')], verbose_name='Action Type')),
                ('action_type_other', models.CharField(blank=True, help_text="if the action is an unknown type then leave a comment here identifying what the 'other' type is", max_length=50, null=True, verbose_name='Action Other')),
                ('data_collector', models.CharField(blank=True, max_length=100, null=True, verbose_name='Data Collector')),
                ('comment', models.CharField(blank=True, max_length=255, null=True, verbose_name='Comment')),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='actions', to='core.event', verbose_name='Event')),
            ],
        ),
    ]
