# Generated by Django 2.0.4 on 2018-11-08 01:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0002_auto_20181103_1933'),
    ]

    operations = [
        migrations.AddField(
            model_name='index',
            name='type',
            field=models.CharField(choices=[('trail', 'Trail'), ('park', 'Park'), ('municipality', 'Municipality'), ('mountain', 'Mountain'), ('region', 'Region'), ('network', 'Network'), ('location', 'Location')], default='trail', max_length=16),
            preserve_default=False,
        ),
    ]