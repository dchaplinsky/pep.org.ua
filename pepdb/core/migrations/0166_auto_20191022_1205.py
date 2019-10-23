# -*- coding: utf-8 -*-
# Generated by Django 1.11.22 on 2019-10-22 09:05
from __future__ import unicode_literals

from django.db import migrations


def set_rules(apps, schema_editor):
    Rule = apps.get_model("core", "Rule")

    rules = {
        "PEP01": 0.1,
        "PEP02": 0.4,
        "PEP03_home": 0.1,
        "PEP03_land": 0.1,
        "PEP03_avto": 0.4,
        "PEP04_adress": 0.7,
        "PEP04_region": 0.1,
        "PEP05": 0.4,
        "PEP07": 0.8,
        "PEP09": 0.5,
        "PEP10": 0.2,
        "PEP11": 0.2,
        "PEP13": 0.7,
        "PEP15": 0.8,
        "PEP16": 1.0,
        "PEP17": 0.8,
        "PEP18": 0.4,
        "PEP19": 0.6,
        "PEP20": 0.8,
        "PEP21": 1.0,
        "PEP22": 0.8,
        "PEP23": 0.5,
        "PEP24": 1.0,
        "PEP25": 0.7,
        "PEP26": 0.9,
        "PEP27": 0.3,
    }

    for k, weight in rules.items():
        Rule.objects.create(pk=k, weight=weight)


def destroy_rules(apps, schema_editor):
    Rule = apps.get_model("core", "Rule")
    Rule.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [("core", "0165_auto_20191022_1156")]

    operations = [migrations.RunPython(set_rules, reverse_code=destroy_rules)]