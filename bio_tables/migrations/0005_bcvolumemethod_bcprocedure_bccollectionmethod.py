# Generated by Django 4.2 on 2023-11-21 13:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bio_tables', '0004_alter_bclifehistory_data_center_code_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='BCVolumeMethod',
            fields=[
                ('volume_method_seq', models.IntegerField(help_text='Volume method code value.', primary_key=True, serialize=False)),
                ('name', models.CharField(help_text='Volume method name.', max_length=30)),
                ('description', models.CharField(blank=True, help_text='Volume method description.', max_length=1000, null=True)),
                ('data_center_code', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='volume_method_codes', to='bio_tables.bcdatacenter', verbose_name='Data Center')),
            ],
        ),
        migrations.CreateModel(
            name='BCProcedure',
            fields=[
                ('procedure_seq', models.IntegerField(help_text='Procedure code value.', primary_key=True, serialize=False)),
                ('name', models.CharField(help_text='Procedure name.', max_length=30)),
                ('description', models.CharField(blank=True, help_text='Procedure description.', max_length=1000, null=True)),
                ('data_center_code', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='procedure_codes', to='bio_tables.bcdatacenter', verbose_name='Data Center')),
            ],
        ),
        migrations.CreateModel(
            name='BCCollectionMethod',
            fields=[
                ('collection_method_seq', models.IntegerField(help_text='Auto generated sequence number.', primary_key=True, serialize=False)),
                ('name', models.CharField(help_text='Common name of the collection method.', max_length=30)),
                ('description', models.CharField(blank=True, help_text='Description of the collection method code.', max_length=1000, null=True)),
                ('data_center_code', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='collection_method_codes', to='bio_tables.bcdatacenter', verbose_name='Data Center')),
            ],
        ),
    ]
