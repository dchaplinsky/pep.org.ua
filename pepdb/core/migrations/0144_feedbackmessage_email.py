# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-04-04 21:37
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0143_auto_20180403_1255'),
    ]

    operations = [
        migrations.AddField(
            model_name='feedbackmessage',
            name='email',
            field=models.EmailField(blank=True, max_length=512, verbose_name='e-mail'),
        ),
    ]