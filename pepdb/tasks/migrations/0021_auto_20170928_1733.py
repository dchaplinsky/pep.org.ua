# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-09-28 14:33
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0020_auto_20170928_1531'),
    ]

    operations = [
        migrations.AlterIndexTogether(
            name='companydeduplication',
            index_together=set([('company1_id', 'company2_id')]),
        ),
    ]
