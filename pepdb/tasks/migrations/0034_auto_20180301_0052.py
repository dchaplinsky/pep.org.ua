# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-02-28 22:52
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0033_terminationnotice_comments'),
    ]

    operations = [
        migrations.AlterField(
            model_name='terminationnotice',
            name='pep_position',
            field=models.TextField(blank=True, null=True, verbose_name='\u041f\u043e\u0441\u0430\u0434\u0430'),
        ),
    ]
