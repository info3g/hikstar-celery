# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-12-21 17:11
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('utils', '0003_merge_20161201_1437'),
    ]

    operations = [
        migrations.AddField(
            model_name='image',
            name='credit',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
