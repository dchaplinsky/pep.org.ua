# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-09-28 12:31
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tasks', '0019_auto_20170925_0058'),
    ]

    operations = [
        migrations.CreateModel(
            name='CompanyDeduplication',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True, verbose_name='\u0421\u0442\u0432\u043e\u0440\u0435\u043d\u043e')),
                ('last_modified', models.DateTimeField(auto_now=True, null=True, verbose_name='\u0417\u043c\u0456\u043d\u0435\u043d\u043e')),
                ('status', models.CharField(choices=[('p', '\u041d\u0435 \u043f\u0435\u0440\u0435\u0432\u0456\u0440\u0435\u043d\u043e'), ('m', "\u041e\u0431'\u0454\u0434\u043d\u0430\u0442\u0438"), ('a', '\u0417\u0430\u043b\u0438\u0448\u0438\u0442\u0438 \u0432\u0441\u0435 \u044f\u043a \u0454'), ('p1', '\u041f\u0435\u0440\u0448\u0430 \u0454 \u043f\u0440\u0430\u0432\u043e\u043d\u0430\u0441\u0442\u0443\u043f\u043d\u0438\u0446\u0435\u044e'), ('p2', '\u0414\u0440\u0443\u0433\u0430 \u0454 \u043f\u0440\u0430\u0432\u043e\u043d\u0430\u0441\u0442\u0443\u043f\u043d\u0438\u0446\u0435\u044e'), ('-', '---------------'), ('d1', '\u0412\u0438\u0434\u0430\u043b\u0438\u0442\u0438 \u043f\u0435\u0440\u0448\u0443'), ('d2', '\u0412\u0438\u0434\u0430\u043b\u0438\u0442\u0438 \u0434\u0440\u0443\u0433\u0443'), ('dd', '\u0412\u0438\u0434\u0430\u043b\u0438\u0442\u0438 \u0432\u0441\u0456')], db_index=True, default='p', max_length=2, verbose_name='\u0421\u0442\u0430\u0442\u0443\u0441')),
                ('company1_id', models.IntegerField(null=True)),
                ('company2_id', models.IntegerField(null=True)),
                ('fuzzy', models.BooleanField(db_index=True, default=False)),
                ('applied', models.BooleanField(db_index=True, default=False)),
                ('company1_json', jsonfield.fields.JSONField(null=True, verbose_name='\u041a\u043e\u043c\u043f\u0430\u043d\u0456\u044f 1')),
                ('company2_json', jsonfield.fields.JSONField(null=True, verbose_name='\u041a\u043e\u043c\u043f\u0430\u043d\u0456\u044f 2')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='\u041a\u043e\u0440\u0438\u0441\u0442\u0443\u0432\u0430\u0447')),
            ],
            options={
                'verbose_name': '\u0414\u0443\u0431\u043b\u0456\u043a\u0430\u0442 \u044e\u0440\u0438\u0434\u0438\u0447\u043d\u0438\u0445 \u043e\u0441\u0456\u0431',
                'verbose_name_plural': '\u0414\u0443\u0431\u043b\u0456\u043a\u0430\u0442\u0438 \u044e\u0440\u0438\u0434\u0438\u0447\u043d\u0438\u0445 \u043e\u0441\u0456\u0431',
            },
        ),
        migrations.AlterUniqueTogether(
            name='companydeduplication',
            unique_together=set([('company1_id', 'company2_id')]),
        ),
    ]
