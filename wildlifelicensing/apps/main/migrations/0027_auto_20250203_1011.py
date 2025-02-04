# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2025-02-03 02:11
from __future__ import unicode_literals

from django.db import migrations

def copy_ledger_licence_types(apps, schema_editor):
    BaseLicenceType = apps.get_model('wl_main', 'BaseLicenceType')
    LicenceType = apps.get_model('licence', 'LicenceType')

    for licence_type in LicenceType.objects.all():
        BaseLicenceType.objects.create(
            pk=licence_type.pk,
            name=licence_type.name,
            short_name=licence_type.short_name,
            version=licence_type.version,
            code=licence_type.code,
            act=licence_type.act,
            statement=licence_type.statement,
            authority=licence_type.authority,
            is_renewable=licence_type.is_renewable,
            keywords=licence_type.keywords
        )

class Migration(migrations.Migration):

    dependencies = [
        ('wl_main', '0026_auto_20250203_1006'),
    ]

    operations = [
        migrations.RunPython(copy_ledger_licence_types),
    ]
