# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-10-21 16:39
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('location', '0002_auto_20161021_1526'),
    ]

    operations = [
        migrations.AlterField(
            model_name='location',
            name='objectid',
            field=models.IntegerField(null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='pointofinterest',
            name='objectid',
            field=models.IntegerField(null=True, unique=True),
        ),
    ]