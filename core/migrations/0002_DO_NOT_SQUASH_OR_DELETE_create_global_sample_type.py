# Generated by Django 4.2 on 2023-12-21 15:27

from django.db import migrations, models, transaction
import django.db.models.deletion


def write_bulk_update(model, update_list, fields):
    if len(update_list) > 0:
        with transaction.atomic():
            model.objects.bulk_update(update_list, fields)
            return True

    return False


def update_mission_defaults(apps, schema_editor):
    MissionSampleType = apps.get_model('core', 'MissionSampleType')

    fields = ["name", "long_name", "priority", "is_sensor", "datatype"]
    bulk_update_list = []
    for mission_sample_type in MissionSampleType.objects.all().iterator():
        mission_sample_type.name = mission_sample_type.sample_type.short_name
        mission_sample_type.long_name = mission_sample_type.sample_type.long_name
        mission_sample_type.priority = mission_sample_type.sample_type.priority
        mission_sample_type.is_sensor = mission_sample_type.sample_type.is_sensor
        mission_sample_type.datatype = mission_sample_type.sample_type.datatype
        bulk_update_list.append(mission_sample_type)

        if write_bulk_update(MissionSampleType, bulk_update_list, fields):
            bulk_update_list = []

    write_bulk_update(MissionSampleType, bulk_update_list, fields)


def reverse_mission_sampletype_delete(apps, schema_editor):
    MissionSampleType = apps.get_model('core', 'MissionSampleType')
    GlobalSampleType = apps.get_model('core', 'GlobalSampleType')
    sample_types = {st.short_name: st for st in GlobalSampleType.objects.all()}

    fields = ["sample_type"]
    bulk_update_list = []
    for mission_sample_type in MissionSampleType.objects.all().iterator():
        mission_sample_type.sample_type = sample_types[mission_sample_type.name]
        bulk_update_list.append(mission_sample_type)

        if write_bulk_update(MissionSampleType, bulk_update_list, fields):
            bulk_update_list = []

    write_bulk_update(MissionSampleType, bulk_update_list, fields)


def reverse_biochemupload_mission_delete(apps, schema_editor):
    MissionSampleType = apps.get_model('core', 'MissionSampleType')
    BioChemUpload = apps.get_model('core', 'BioChemUpload')
    sample_types = {st.name: st.mission for st in MissionSampleType.objects.all()}

    fields = ["mission"]
    bulk_update_list = []
    for upload in BioChemUpload.objects.all().iterator():
        upload.mission = sample_types[upload.type.short_name]
        bulk_update_list.append(upload)

        if write_bulk_update(BioChemUpload, bulk_update_list, fields):
            bulk_update_list = []

    write_bulk_update(BioChemUpload, bulk_update_list, fields)


def update_missionsampletype(model, apps, get_mission):
    MissionSampleType = apps.get_model('core', 'MissionSampleType')
    sample_types = {st.name: st for st in MissionSampleType.objects.all()}

    fields = ["missionsampletype"]
    bulk_update_list = []
    for obj in model.objects.all().iterator():
        if obj.type.short_name not in sample_types.keys():
            mission = get_mission(obj)
            mst = MissionSampleType(mission=mission, name=obj.type.short_name, long_name=obj.type.long_name,
                                    priority=obj.type.priority, is_sensor=obj.type.is_sensor,
                                    datatype=obj.type.datatype)
            obj.missionsampletype = mst
            with transaction.atomic():
                mst.save()
        else:
            obj.missionsampletype = sample_types[obj.type.short_name]

        bulk_update_list.append(obj)

        if write_bulk_update(model, bulk_update_list, fields):
            bulk_update_list = []

    write_bulk_update(model, bulk_update_list, fields)


def update_sample_sample_type(apps, schema_editor):
    Sample = apps.get_model('core', 'Sample')

    def get_mission(sample):
        return sample.bottle.event.mission

    update_missionsampletype(Sample, apps, get_mission)


def update_biochem_sample_type(apps, schema_editor):
    BioChemUpload = apps.get_model('core', 'BioChemUpload')

    def get_mission(biochemupload):
        return biochemupload.mission

    update_missionsampletype(BioChemUpload, apps, get_mission)


def reverse_sampletype_delete(model, apps):
    GlobalSampleType = apps.get_model('core', 'GlobalSampleType')
    sample_types = {st.short_name: st for st in GlobalSampleType.objects.all()}

    fields = ["type"]
    bulk_update_list = []
    new_gst = {}
    for obj in model.objects.all().iterator():
        mission_type = obj.missionsampletype
        if mission_type.name in sample_types.keys():
            obj.type = sample_types[mission_type.name]
        elif mission_type.name in new_gst.keys():
            obj.type = new_gst[mission_type.name]
        else:
            gst = GlobalSampleType(short_name=mission_type.name, long_name=mission_type.long_name,
                                   priority=mission_type.priority, is_sensor=mission_type.is_sensor,
                                   datatype=mission_type.datatype)
            with transaction.atomic():
                gst.save()

            new_gst[mission_type.name] = gst
            obj.type = gst

        bulk_update_list.append(obj)

        if write_bulk_update(model, bulk_update_list, fields):
            bulk_update_list = []

    write_bulk_update(model, bulk_update_list, fields)


def reverse_sample_type_delete(apps, schema_editor):
    model = apps.get_model('core', 'Sample')
    reverse_sampletype_delete(model, apps)


def reverse_biochemupload_type_delete(apps, schema_editor):
    model = apps.get_model('core', 'BioChemUpload')
    reverse_sampletype_delete(model, apps)


class Migration(migrations.Migration):

    dependencies = [
        ('bio_tables', '0005_bcvolumemethod_bcprocedure_bccollectionmethod'),
        ('core', '0001_squashed_0022_alter_biochemupload_modified_date'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='SampleType',
            new_name='GlobalSampleType',
        ),
        migrations.RemoveField(
            model_name='globalsampletype',
            name='comments',
        ),
        migrations.AddField(
            model_name='missionsampletype',
            name='is_sensor',
            field=models.BooleanField(default=False, help_text='Identify this sample type as a type of sensor',
                                      verbose_name='Is Sensor'),
        ),
        migrations.AddField(
            model_name='missionsampletype',
            name='long_name',
            field=models.CharField(blank=True, help_text='Short descriptive name for this type of sample/sensor',
                                   max_length=126, null=True, verbose_name='Name'),
        ),
        migrations.AddField(
            model_name='missionsampletype',
            name='name',
            field=models.CharField(help_text='The column name of a sensor or a short name commonly used for the sample',
                                   max_length=20, null=True, verbose_name='Short/Column Name'),
        ),
        migrations.AddField(
            model_name='missionsampletype',
            name='priority',
            field=models.IntegerField(default=1, verbose_name='Priority'),
        ),
        migrations.RunPython(update_mission_defaults, lambda apps, schema_editor:()),
        migrations.AlterField(
            model_name='missionsampletype',
            name='sample_type',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE,
                                    related_name='mission_sample_types', to='core.globalsampletype',
                                    verbose_name='Sample Type'),
        ),
        migrations.RunPython(lambda apps, schema_editor:(), reverse_mission_sampletype_delete),
        migrations.RemoveField(
            model_name='missionsampletype',
            name='sample_type',
        ),

        migrations.AlterField(
            model_name='biochemupload',
            name='mission',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE,
                                    related_name='uploads', to='core.mission',
                                    verbose_name='Mission'),
        ),
        migrations.RunPython(lambda apps, schema_editor:(), reverse_biochemupload_mission_delete),
        migrations.RemoveField(
            model_name='biochemupload',
            name='mission',
        ),

        # Modify the Sample model to swap out the GlobalSampleType
        migrations.AddField(
            model_name='sample',
            name='missionsampletype',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='samples',
                                    to='core.missionsampletype', verbose_name='Sample Type'),
        ),
        migrations.RunPython(update_sample_sample_type, lambda apps, schema_editor:()),
        migrations.AlterField(
            model_name='sample',
            name='type',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE,
                                    related_name='samples', to='core.globalsampletype',
                                    verbose_name='Type'),
        ),
        migrations.AlterField(
            model_name='sample',
            name='missionsampletype',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='samples',
                                    to='core.missionsampletype', verbose_name='Sample Type'),
        ),
        migrations.RunPython(lambda apps, schema_editor:(), reverse_sample_type_delete),
        migrations.RemoveField(
            model_name='sample',
            name='type',
        ),
        migrations.RenameField(
            model_name='sample',
            old_name='missionsampletype',
            new_name='type',
        ),

        # Modify the BioChemUpload model to swap out the GlobalSampleType
        migrations.AddField(
            model_name='biochemupload',
            name='missionsampletype',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='uploads',
                                    to='core.missionsampletype', verbose_name='Sample Type'),
        ),
        migrations.RunPython(update_biochem_sample_type, lambda apps, schema_editor:()),
        migrations.AlterField(
            model_name='biochemupload',
            name='type',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE,
                                    related_name='samples', to='core.globalsampletype',
                                    verbose_name='Type'),
        ),
        migrations.AlterField(
            model_name='biochemupload',
            name='missionsampletype',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='uploads',
                                    to='core.missionsampletype', verbose_name='Sample Type'),
        ),
        migrations.RunPython(lambda apps, schema_editor:(), reverse_biochemupload_type_delete),
        migrations.RemoveField(
            model_name='biochemupload',
            name='type',
        ),
        migrations.RenameField(
            model_name='biochemupload',
            old_name='missionsampletype',
            new_name='type',
        ),
    ]
