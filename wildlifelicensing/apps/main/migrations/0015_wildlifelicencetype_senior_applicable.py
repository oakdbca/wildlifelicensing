# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-08-30 07:28
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wl_main', '0014_communicationslogentry_cc'),
    ]

    operations = [
        migrations.AddField(
            model_name='wildlifelicencetype',
            name='senior_applicable',
            field=models.BooleanField(default=False),
        ),
    ]
