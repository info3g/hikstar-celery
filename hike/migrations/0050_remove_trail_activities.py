# Generated by Django 2.0.4 on 2018-11-10 22:49

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hike', '0049_auto_20181110_2246'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='trail',
            name='activities',
        ),
    ]