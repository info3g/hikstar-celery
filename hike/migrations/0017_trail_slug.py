# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-16 15:02
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hike', '0016_auto_20170207_1941'),
    ]

    operations = [
        migrations.AddField(
            model_name='trail',
            name='slug',
            field=models.SlugField(blank=True, default='', max_length=300),
        ),
    ]
