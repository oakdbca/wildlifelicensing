# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2025-02-05 03:30
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wl_main', '0053_auto_20250205_1055'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='communicationslogentry',
            name='documents',
        ),
    ]
