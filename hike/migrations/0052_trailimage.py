# Generated by Django 2.0.4 on 2018-11-23 01:39

from django.db import migrations, models
import django.db.models.deletion
import easy_thumbnails.fields


class Migration(migrations.Migration):

    dependencies = [
        ('hike', '0051_auto_20181110_2250'),
    ]

    operations = [
        migrations.CreateModel(
            name='TrailImage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image_type', models.CharField(max_length=20)),
                ('image', easy_thumbnails.fields.ThumbnailerImageField(max_length=300, upload_to='images/')),
                ('credit', models.CharField(blank=True, max_length=255, null=True)),
                ('trail', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='hike.Trail')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
