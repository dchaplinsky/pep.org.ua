# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.core.management.base import BaseCommand
from core.models import Ua2EnDictionary
from unicodecsv import reader
from django.db.models import F, Func, Value


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            'file_path',
            help='CSV file to import translations',
        )
        parser.add_argument(
            '--replace',
            default=False,
            action="store_true",
            help='Replace existing non-empty translations',
        )

    def handle(self, *args, **options):
        file_path = options['file_path']
        successful = 0
        failed = 0

        with open(file_path, "r") as fp:
            r = reader(fp)

            for term, trans in r[:2]:
                term = term.strip()
                trans = trans.strip()

                if term and trans:
                    try:
                        obj = Ua2EnDictionary.objects.get(term=term)
                    except Ua2EnDictionary.DoesNotExist:
                        self.stderr.write("Cannot find term %s in db, falling back to fuzzier search" % term)
                        term = term.replace(" ", "")

                        try:
                            obj = Ua2EnDictionary.objects.annotate(
                                term_key=Func(F('term'), Value(' '), Value(''), function='replace')).get(term_key=term)
                        except Ua2EnDictionary.MultipleObjectsReturned:
                            self.stderr.write("More than one result for term %s in db" % term)
                            failed += 1
                            continue
                        except Ua2EnDictionary.DoesNotExist:
                            self.stderr.write("Cannot find term %s in db, falling back to fuzzier search" % term)
                            failed += 1
                            continue
                    except Ua2EnDictionary.MultipleObjectsReturned:
                        self.stderr.write("More than one result for term %s in db" % term)
                        failed += 1
                        continue

                    if obj.translation:
                        if obj.translation.lower() == trans.lower():
                            continue

                        if not options["replace"]:
                            self.stdout.write(
                                "Not overwritting existing translation %s for term %s with %s" % (
                                    term, obj.translation, trans))
                            failed += 1
                            continue

                    obj.translation = trans
                    obj.save()
                    successful += 1

            self.stdout.write("Import is done, successful: %s, failed: %s" % (successful, failed))
