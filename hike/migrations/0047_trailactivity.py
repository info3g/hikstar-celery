# Generated by Django 2.0.4 on 2018-11-10 20:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hike', '0046_trail_shape_simplified'),
    ]

    operations = [
        migrations.CreateModel(
            name='TrailActivity',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('difficulty', models.IntegerField(blank=True, choices=[(1, 'Débutant'), (2, 'Modéré'), (3, 'Intermédiaire'), (4, 'Soutenu'), (5, 'Exigeant')], null=True)),
                ('duration', models.IntegerField(help_text='Duration, in seconds', null=True)),
                ('activity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='hike.Activity')),
                ('trail', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='hike.Trail')),
            ],
        ),
    ]