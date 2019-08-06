# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-05-12 11:45
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0155_auto_20190205_1344'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='relationshipproof',
            options={'verbose_name': '\u041f\u043e\u0441\u0438\u043b\u0430\u043d\u043d\u044f \u0430\u0431\u043e \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442', 'verbose_name_plural': '\u041f\u043e\u0441\u0438\u043b\u0430\u043d\u043d\u044f \u0430\u0431\u043e \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u0438'},
        ),
        migrations.AddField(
            model_name='feedbackmessage',
            name='read_and_agreed',
            field=models.BooleanField(default=False, verbose_name='\u041a\u043e\u0440\u0438\u0441\u0442\u0443\u0432\u0430\u0447 \u043f\u0456\u0434\u0442\u0432\u0435\u0440\u0434\u0438\u0432 \u0449\u043e \u043f\u0440\u043e\u0447\u0438\u0442\u0430\u0432 \u0447\u0430\u0441\u0442\u043e \u0437\u0430\u0434\u0430\u0432\u0430\u0454\u043c\u0456 \u043f\u0438\u0442\u0430\u043d\u043d\u044f'),
        ),
        migrations.AlterField(
            model_name='relationshipproof',
            name='proof',
            field=models.TextField(blank=True, verbose_name='\u0430\u0431\u043e \u043f\u043e\u0441\u0438\u043b\u0430\u043d\u043d\u044f'),
        ),
        migrations.AlterField(
            model_name='relationshipproof',
            name='proof_document',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.Document', verbose_name='\u0424\u0430\u0439\u043b \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u0430'),
        ),
        migrations.AlterField(
            model_name='relationshipproof',
            name='proof_title',
            field=models.TextField(blank=True, help_text='\u041d\u0430\u043f\u0440\u0438\u043a\u043b\u0430\u0434: \u0441\u043a\u043b\u0430\u0434 \u0412\u0420 7-\u0433\u043e \u0441\u043a\u043b\u0438\u043a\u0430\u043d\u043d\u044f', verbose_name='\u041d\u0430\u0437\u0432\u0430 \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u0430 \u0430\u0431\u043e \u043f\u043e\u0441\u0438\u043b\u0430\u043d\u043d\u044f'),
        ),
        migrations.AlterField(
            model_name='relationshipproof',
            name='proof_title_en',
            field=models.TextField(blank=True, help_text='\u041d\u0430\u043f\u0440\u0438\u043a\u043b\u0430\u0434: \u0441\u043a\u043b\u0430\u0434 \u0412\u0420 7-\u0433\u043e \u0441\u043a\u043b\u0438\u043a\u0430\u043d\u043d\u044f', null=True, verbose_name='\u041d\u0430\u0437\u0432\u0430 \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u0430 \u0430\u0431\u043e \u043f\u043e\u0441\u0438\u043b\u0430\u043d\u043d\u044f'),
        ),
        migrations.AlterField(
            model_name='relationshipproof',
            name='proof_title_uk',
            field=models.TextField(blank=True, help_text='\u041d\u0430\u043f\u0440\u0438\u043a\u043b\u0430\u0434: \u0441\u043a\u043b\u0430\u0434 \u0412\u0420 7-\u0433\u043e \u0441\u043a\u043b\u0438\u043a\u0430\u043d\u043d\u044f', null=True, verbose_name='\u041d\u0430\u0437\u0432\u0430 \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u0430 \u0430\u0431\u043e \u043f\u043e\u0441\u0438\u043b\u0430\u043d\u043d\u044f'),
        ),
    ]