# -*- coding: utf-8 -*-
# Generated by Django 1.11.18 on 2019-02-05 11:44
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0154_auto_20181020_2039'),
    ]

    operations = [
        migrations.AddField(
            model_name='person',
            name='inn',
            field=models.CharField(blank=True, max_length=40, null=True, verbose_name='\u0406\u041f\u041d \u0437 \u043f\u0443\u0431\u043b\u0456\u0447\u043d\u0438\u0445 \u0434\u0436\u0435\u0440\u0435\u043b'),
        ),
        migrations.AddField(
            model_name='person',
            name='inn_source',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='inns', to='core.Document', verbose_name='\u0414\u043e\u043a\u0443\u043c\u0435\u043d\u0442 \u0437 \u043a\u043e\u0442\u0440\u043e\u0433\u043e \u0431\u0443\u043b\u043e \u043e\u0442\u0440\u0438\u043c\u0430\u043d\u043e \u0406\u041f\u041d'),
        ),
        migrations.AddField(
            model_name='person',
            name='passport',
            field=models.CharField(blank=True, max_length=40, null=True, verbose_name='\u041f\u0430\u0441\u043f\u043e\u0440\u0442\u043d\u0456 \u0434\u0430\u043d\u0456 \u0437 \u043f\u0443\u0431\u043b\u0456\u0447\u043d\u0438\u0445 \u0434\u0436\u0435\u0440\u0435\u043b'),
        ),
        migrations.AddField(
            model_name='person',
            name='passport_source',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='passports', to='core.Document', verbose_name='\u0414\u043e\u043a\u0443\u043c\u0435\u043d\u0442 \u0437 \u043a\u043e\u0442\u0440\u043e\u0433\u043e \u0431\u0443\u043b\u043e \u043e\u0442\u0440\u0438\u043c\u0430\u043d\u043e \u0406\u041f\u041d'),
        ),
    ]