# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-03-01 11:51
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0034_auto_20180301_0052'),
    ]

    operations = [
        migrations.AddField(
            model_name='terminationnotice',
            name='termination_date_ceiled',
            field=models.DateField(blank=True, null=True, verbose_name='\u0414\u0430\u0442\u0430 \u043f\u0440\u0438\u043f\u0438\u043d\u0435\u043d\u043d\u044f \u0441\u0442\u0430\u0442\u0443\u0441\u0443 \u041f\u0415\u041f, \u043e\u043a\u0440\u0443\u0433\u043b\u0435\u043d\u0430 \u0432\u0433\u043e\u0440\u0443'),
        ),
    ]
