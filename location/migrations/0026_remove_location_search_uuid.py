# Generated by Django 2.0.4 on 2018-11-10 22:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('location', '0025_auto_20181110_2044'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='location',
            name='search_uuid',
        ),
    ]