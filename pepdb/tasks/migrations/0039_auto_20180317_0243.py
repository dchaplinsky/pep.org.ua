# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-03-17 00:43
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0038_adhocmatches'),
    ]

    operations = [
        migrations.RenameField(
            model_name='adhocmatches',
            old_name='match_json',
            new_name='matched_json',
        ),
    ]
