# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-07-11 14:32
import django.contrib.gis.db.models.fields
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('hike', '0020_auto_20170307_2128'),
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('event_id', models.AutoField(primary_key=True, serialize=False)),
                ('date_insert', models.DateTimeField(auto_now_add=True)),
                ('date_update', models.DateTimeField(auto_now=True)),
                ('deleted', models.BooleanField(default=False, editable=False)),
                ('shape', django.contrib.gis.db.models.fields.GeometryField(blank=True, default=None, dim=3, null=True, srid=4326)),
                ('lgth', models.FloatField(blank=True, default=0.0, editable=False, null=True)),
                ('ascent', models.IntegerField(blank=True, default=0, editable=False, null=True)),
                ('descent', models.IntegerField(blank=True, default=0, editable=False, null=True)),
                ('min_elevation', models.IntegerField(blank=True, default=0, editable=False, null=True)),
                ('max_elevation', models.IntegerField(blank=True, default=0, editable=False, null=True)),
                ('slope', models.FloatField(blank=True, default=0.0, editable=False, null=True)),
                ('e_offset', models.FloatField(default=0.0)),
                ('kind', models.CharField(editable=False, max_length=32)),
                ('shape_2d', django.contrib.gis.db.models.fields.GeometryField(default=None, editable=False, null=True, srid=4326)),
            ],
        ),
        migrations.CreateModel(
            name='EventTrailSection',
            fields=[
                ('eventtrailsection_id', models.AutoField(primary_key=True, serialize=False)),
                ('start_position', models.FloatField(db_index=True)),
                ('end_position', models.FloatField(db_index=True)),
                ('order', models.IntegerField(blank=True, default=0, null=True)),
                ('evnt', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='hike.Event')),
            ],
        ),
        migrations.RenameField(
            model_name='trailsection',
            old_name='trail_id',
            new_name='trailsection_id',
        ),
        migrations.RemoveField(
            model_name='trailsection',
            name='length',
        ),
        migrations.AddField(
            model_name='trailsection',
            name='arrival',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
        migrations.AddField(
            model_name='trailsection',
            name='ascent',
            field=models.IntegerField(blank=True, default=0, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='trailsection',
            name='comments',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='trailsection',
            name='date_insert',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='trailsection',
            name='date_update',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='trailsection',
            name='departure',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
        migrations.AddField(
            model_name='trailsection',
            name='descent',
            field=models.IntegerField(blank=True, default=0, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='trailsection',
            name='external_id',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='trailsection',
            name='lgth',
            field=models.FloatField(blank=True, default=0.0, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='trailsection',
            name='max_elevation',
            field=models.IntegerField(blank=True, default=0, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='trailsection',
            name='min_elevation',
            field=models.IntegerField(blank=True, default=0, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='trailsection',
            name='name',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='trailsection',
            name='shape_2d',
            field=django.contrib.gis.db.models.fields.LineStringField(null=True, srid=4326),
        ),
        migrations.AddField(
            model_name='trailsection',
            name='slope',
            field=models.FloatField(blank=True, default=0.0, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='trailsection',
            name='valid',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='trailsection',
            name='visible',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='eventtrailsection',
            name='trailsection',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='hike.TrailSection'),
        ),
        migrations.AddField(
            model_name='event',
            name='trailsections',
            field=models.ManyToManyField(through='hike.EventTrailSection', to='hike.TrailSection'),
        ),
    ]