# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-03-17 13:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0041_auto_20180317_0302'),
    ]

    operations = [
        migrations.AlterField(
            model_name='adhocmatch',
            name='status',
            field=models.CharField(choices=[('p', '\u041d\u0435 \u043f\u0435\u0440\u0435\u0432\u0456\u0440\u0435\u043d\u043e'), ('a', '\u0417\u0430\u0441\u0442\u043e\u0441\u043e\u0432\u0430\u043d\u043e'), ('i', '\u0406\u0433\u043d\u043e\u0440\u0443\u0432\u0430\u0442\u0438'), ('r', '\u041f\u043e\u0442\u0440\u0435\u0431\u0443\u0454 \u0434\u043e\u0434\u0430\u0442\u043a\u043e\u0432\u043e\u0457 \u043f\u0435\u0440\u0435\u0432\u0456\u0440\u043a\u0438')], db_index=True, default='p', max_length=1, verbose_name='\u0421\u0442\u0430\u0442\u0443\u0441'),
        ),
    ]
