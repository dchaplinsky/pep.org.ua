# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.core.management.base import BaseCommand

from tqdm import tqdm

from core.models import Person2Company, Company


class Command(BaseCommand):
    help = "Check if the head of the company in DB matches those in the EDR"

    def handle(self, *args, **options):
        qs = Person2Company.objects.filter(category="other")

        for p2c in tqdm(qs, total=qs.count()):
            old_cat = p2c.relationship_category

            if old_cat not in ["ex_owner", "other"]:
                p2c.category = old_cat
                p2c.save()
                continue

            if any(
                map(
                    lambda x: x.search(p2c.relationship_type_uk.lower()),
                    Company.HEADS_CLASSIFIERS,
                )
            ):
                p2c.category = "manager"
                p2c.save()
                continue
