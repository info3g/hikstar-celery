# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-12-20 19:56
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('location', '0013_locationlimbo_is_modified'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='locationlimbo',
            name='address',
        ),
        migrations.RemoveField(
            model_name='locationlimbo',
            name='contact',
        ),
        migrations.RemoveField(
            model_name='locationlimbo',
            name='images',
        ),
        migrations.RemoveField(
            model_name='locationlimbo',
            name='original',
        ),
        migrations.DeleteModel(
            name='LocationLimbo',
        ),
    ]
