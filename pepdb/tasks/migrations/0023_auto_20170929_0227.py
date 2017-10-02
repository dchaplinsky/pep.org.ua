# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-09-28 23:27
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0022_auto_20170929_0137'),
    ]

    operations = [
        migrations.AlterField(
            model_name='beneficiariesmatching',
            name='company_key',
            field=models.CharField(max_length=500, verbose_name='\u041a\u043b\u044e\u0447 \u043a\u043e\u043c\u043f\u0430\u043d\u0456\u0457'),
        ),
        migrations.AlterUniqueTogether(
            name='beneficiariesmatching',
            unique_together=set([('company_key', 'type_of_connection')]),
        ),
    ]