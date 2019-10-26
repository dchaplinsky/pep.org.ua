# -*- coding: utf-8 -*-
# Generated by Django 1.11.22 on 2019-10-24 12:43
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0169_auto_20191024_1523'),
    ]

    operations = [
        migrations.AlterField(
            model_name='article',
            name='related_companies',
            field=models.ManyToManyField(to='core.Company', verbose_name="\u041f\u043e\u0432'\u044f\u0437\u0430\u043d\u0456 \u043a\u043e\u043c\u043f\u0430\u043d\u0456\u0457"),
        ),
        migrations.AlterField(
            model_name='article',
            name='related_persons',
            field=models.ManyToManyField(to='core.Person', verbose_name="\u041f\u043e\u0432'\u044f\u0437\u0430\u043d\u0456 \u043e\u0441\u043e\u0431\u0438"),
        ),
    ]