# Generated by Django 4.2 on 2024-07-30 11:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('biochem', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Bcactivityedits',
            fields=[
                ('activity_edt_seq', models.BigIntegerField(primary_key=True, serialize=False)),
                ('event_edt_seq', models.BigIntegerField()),
                ('event_seq', models.BigIntegerField(blank=True, null=True)),
                ('activity_seq', models.BigIntegerField(blank=True, null=True)),
                ('data_center_code', models.IntegerField(blank=True, null=True)),
                ('data_pointer_code', models.CharField(blank=True, max_length=2, null=True)),
                ('process_flag', models.CharField(max_length=3)),
                ('batch_seq', models.IntegerField(blank=True, null=True)),
            ],
            options={
                'db_table': 'BCACTIVITYEDITS',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Bcbatches',
            fields=[
                ('batch_seq', models.IntegerField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=30)),
                ('description', models.CharField(blank=True, max_length=250, null=True)),
                ('username', models.CharField(max_length=30)),
            ],
            options={
                'db_table': 'BCBATCHES',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Bcerrorcodes',
            fields=[
                ('error_code', models.IntegerField(db_comment='Code that specifies the validation error in the Edit table system.', primary_key=True, serialize=False)),
                ('description', models.CharField(db_comment='Description of the validation error.', max_length=80)),
                ('long_desc', models.CharField(blank=True, db_comment='Detailed description of the validation error.', max_length=300, null=True)),
                ('last_update_by', models.CharField(db_comment='The user id of the user who last updated the Codes in the ERROR_CODE table.', max_length=30)),
                ('last_update_date', models.DateField(db_comment='The date that the last update took place to a specified record in the ERROR_CODE table.')),
            ],
            options={
                'db_table': 'BCERRORCODES',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Bcerrors',
            fields=[
                ('error_num_seq', models.IntegerField(primary_key=True, serialize=False)),
                ('edit_table_name', models.CharField(max_length=30)),
                ('record_num_seq', models.BigIntegerField()),
                ('column_name', models.CharField(max_length=30)),
                ('error_code', models.IntegerField()),
                ('last_updated_by', models.CharField(max_length=30)),
                ('last_update_date', models.DateField()),
                ('batch_seq', models.IntegerField()),
            ],
            options={
                'db_table': 'BCERRORS',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Bcstatndataerrors',
            fields=[
                ('statn_data_table_name', models.CharField(max_length=30)),
                ('record_sequence_value', models.CharField(max_length=50, primary_key=True, serialize=False)),
                ('column_name', models.CharField(max_length=30)),
                ('error_code', models.IntegerField()),
                ('statn_data_created_date', models.DateField()),
                ('collector_sample_id', models.CharField(max_length=50)),
                ('batch_seq', models.IntegerField()),
            ],
            options={
                'db_table': 'BCSTATNDATAERRORS',
                'managed': False,
            },
        ),
    ]
