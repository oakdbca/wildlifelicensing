# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-06-23 03:14
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        # ('accounts', '0001_initial'),
        # migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('wl_main', '0002_fixtures'),
    ]

    operations = [
        migrations.CreateModel(
            name='CommunicationsLogEntry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('to', models.CharField(blank=True, max_length=200, verbose_name='To')),
                ('fromm', models.CharField(blank=True, max_length=200, verbose_name='From')),
                ('type', models.CharField(choices=[('email', 'Email'), ('phone', 'Phone Call'), ('main', 'Mail'), ('person', 'In Person')], default='email', max_length=20)),
                ('subject', models.CharField(blank=True, max_length=200, verbose_name='Subject / Description')),
                ('text', models.TextField(blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                # ('customer', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='customer', to=settings.AUTH_USER_MODEL)),
                ('customer', models.IntegerField(null=True)),
                # ('document', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='accounts.Document')),
                ('document', models.IntegerField(null=True)),
                # ('officer', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='officer', to=settings.AUTH_USER_MODEL)),
                ('officer', models.IntegerField(null=True)),
            ],
        ),
    ]
