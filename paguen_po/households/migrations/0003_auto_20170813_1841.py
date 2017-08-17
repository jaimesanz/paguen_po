# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-08-13 21:41
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('households', '0002_household_users'),
    ]

    operations = [
        migrations.AlterField(
            model_name='household',
            name='users',
            field=models.ManyToManyField(blank=True, to=settings.AUTH_USER_MODEL),
        ),
    ]
