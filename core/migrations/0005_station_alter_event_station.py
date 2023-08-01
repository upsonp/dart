# Generated by Django 4.2 on 2023-07-29 16:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_event_end_sample_id_event_sample_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='Station',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20, verbose_name='Station')),
            ],
        ),
        migrations.AlterField(
            model_name='event',
            name='station',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='events', to='core.station', verbose_name='Station'),
        ),
    ]
