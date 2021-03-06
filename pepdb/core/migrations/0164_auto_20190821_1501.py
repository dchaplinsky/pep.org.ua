# -*- coding: utf-8 -*-
# Generated by Django 1.11.22 on 2019-08-21 12:01
from __future__ import unicode_literals

from django.db import migrations


def unify_positions(apps, schema_editor):
    Person2Company = apps.get_model("core", "Person2Company")
    Person2Company.objects.filter(relationship_type_uk__iexact="засновники").update(
        relationship_type_uk="Засновник",
        relationship_type_en="Founder"
    )

    Person2Company.objects.filter(relationship_type_uk__iexact="засновник/учасник").update(
        relationship_type_uk="Засновник",
        relationship_type_en="Founder"
    )

    Person2Company.objects.filter(relationship_type_uk__iexact="власники").update(
        relationship_type_uk="Власник",
        relationship_type_en="Owner"
    )

    Person2Company.objects.filter(relationship_type_uk__iexact="співвласність").update(
        relationship_type_uk="Власник",
        relationship_type_en="Owner"
    )

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0163_auto_20190802_0024'),
    ]

    operations = [
        migrations.RunPython(
            unify_positions, reverse_code=migrations.RunPython.noop),
    ]
