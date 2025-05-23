# Generated by Django 4.2 on 2025-02-14 13:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('biochem', '0004_bcplanktndtailedits_bcplanktnfreqedits_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Bcdiscretehedrs',
            fields=[
                ('discrete_seq', models.BigIntegerField(primary_key=True, serialize=False)),
                ('activity_seq', models.IntegerField()),
                ('gear_seq', models.IntegerField()),
                ('start_date', models.DateField()),
                ('end_date', models.DateField(blank=True, null=True)),
                ('start_time', models.IntegerField(blank=True, null=True)),
                ('end_time', models.IntegerField(blank=True, null=True)),
                ('time_qc_code', models.CharField(max_length=2)),
                ('start_lat', models.DecimalField(blank=True, decimal_places=5, max_digits=8, null=True)),
                ('end_lat', models.DecimalField(blank=True, decimal_places=5, max_digits=8, null=True)),
                ('start_lon', models.DecimalField(blank=True, decimal_places=5, max_digits=9, null=True)),
                ('end_lon', models.DecimalField(blank=True, decimal_places=5, max_digits=9, null=True)),
                ('position_qc_code', models.CharField(blank=True, max_length=2, null=True)),
                ('start_depth', models.DecimalField(blank=True, decimal_places=2, max_digits=7, null=True)),
                ('end_depth', models.DecimalField(blank=True, decimal_places=2, max_digits=7, null=True)),
                ('sounding', models.IntegerField()),
                ('collector_deployment_id', models.CharField(blank=True, max_length=50, null=True)),
                ('collector_sample_id', models.CharField(max_length=50)),
                ('collector', models.CharField(blank=True, max_length=50, null=True)),
                ('collector_comment', models.CharField(blank=True, max_length=2000, null=True)),
                ('data_manager_comment', models.CharField(blank=True, max_length=2000, null=True)),
                ('responsible_group', models.CharField(blank=True, max_length=50, null=True)),
                ('prod_created_date', models.DateField()),
                ('shared_data', models.CharField(blank=True, max_length=50, null=True)),
                ('prod_created_by', models.CharField(blank=True, max_length=10, null=True)),
                ('created_date', models.DateField(blank=True, null=True)),
                ('created_by', models.CharField(blank=True, max_length=30, null=True)),
            ],
            options={
                'db_table': 'BCDISCRETEHEDRS',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Bcevents',
            fields=[
                ('event_seq', models.BigIntegerField(primary_key=True, serialize=False)),
                ('start_date', models.DateField(blank=True, null=True)),
                ('end_date', models.DateField(blank=True, null=True)),
                ('start_time', models.IntegerField(blank=True, null=True)),
                ('end_time', models.IntegerField(blank=True, null=True)),
                ('min_lat', models.DecimalField(blank=True, decimal_places=5, max_digits=8, null=True)),
                ('max_lat', models.DecimalField(blank=True, decimal_places=5, max_digits=8, null=True)),
                ('min_lon', models.DecimalField(blank=True, decimal_places=5, max_digits=9, null=True)),
                ('max_lon', models.DecimalField(blank=True, decimal_places=5, max_digits=9, null=True)),
                ('collector_station_name', models.CharField(blank=True, max_length=50, null=True)),
                ('collector_event_id', models.CharField(blank=True, max_length=50, null=True)),
                ('utc_offset', models.DecimalField(blank=True, decimal_places=1, max_digits=4, null=True)),
                ('collector_comment', models.CharField(blank=True, max_length=2000, null=True)),
                ('data_manager_comment', models.CharField(blank=True, max_length=2000, null=True)),
                ('more_comment', models.CharField(default='N', max_length=1)),
                ('prod_created_date', models.DateField(blank=True, null=True)),
                ('prod_created_by', models.CharField(blank=True, max_length=30, null=True)),
                ('created_date', models.DateField(blank=True, null=True)),
                ('created_by', models.CharField(blank=True, max_length=30, null=True)),
            ],
            options={
                'db_table': 'BCEVENTS',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Bcmissions',
            fields=[
                ('mission_seq', models.BigIntegerField(primary_key=True, serialize=False)),
                ('name', models.CharField(blank=True, max_length=50, null=True)),
                ('descriptor', models.CharField(max_length=50)),
                ('leader', models.CharField(blank=True, max_length=50, null=True)),
                ('start_date', models.DateField(blank=True, null=True)),
                ('end_date', models.DateField(blank=True, null=True)),
                ('institute', models.CharField(blank=True, max_length=50, null=True)),
                ('platform', models.CharField(blank=True, max_length=50, null=True)),
                ('protocol', models.CharField(blank=True, max_length=50, null=True)),
                ('geographic_region', models.CharField(blank=True, max_length=100, null=True)),
                ('collector_comment', models.CharField(blank=True, max_length=2000, null=True)),
                ('data_manager_comment', models.CharField(blank=True, max_length=2000, null=True)),
                ('more_comment', models.CharField(default='N', max_length=1)),
                ('prod_created_date', models.DateField()),
                ('prod_created_by', models.CharField(blank=True, max_length=10, null=True)),
                ('created_date', models.DateField(blank=True, null=True)),
                ('created_by', models.CharField(blank=True, max_length=30, null=True)),
            ],
            options={
                'db_table': 'BCMISSIONS',
                'managed': False,
            },
        ),
    ]
