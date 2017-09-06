# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-09-05 11:35
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0112_auto_20170824_0033'),
    ]

    operations = [
        migrations.AlterField(
            model_name='company',
            name='short_name',
            field=models.CharField(blank=True, max_length=200, verbose_name='\u0421\u043a\u043e\u0440\u043e\u0447\u0435\u043d\u0430 \u043d\u0430\u0437\u0432\u0430'),
        ),
        migrations.AlterField(
            model_name='company',
            name='short_name_en',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='\u0421\u043a\u043e\u0440\u043e\u0447\u0435\u043d\u0430 \u043d\u0430\u0437\u0432\u0430'),
        ),
        migrations.AlterField(
            model_name='company',
            name='short_name_uk',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='\u0421\u043a\u043e\u0440\u043e\u0447\u0435\u043d\u0430 \u043d\u0430\u0437\u0432\u0430'),
        ),
        migrations.AlterField(
            model_name='person',
            name='patronymic',
            field=models.CharField(blank=True, max_length=40, verbose_name='\u041f\u043e \u0431\u0430\u0442\u044c\u043a\u043e\u0432\u0456'),
        ),
        migrations.AlterField(
            model_name='person',
            name='patronymic_en',
            field=models.CharField(blank=True, max_length=40, null=True, verbose_name='\u041f\u043e \u0431\u0430\u0442\u044c\u043a\u043e\u0432\u0456'),
        ),
        migrations.AlterField(
            model_name='person',
            name='patronymic_uk',
            field=models.CharField(blank=True, max_length=40, null=True, verbose_name='\u041f\u043e \u0431\u0430\u0442\u044c\u043a\u043e\u0432\u0456'),
        ),
    ]