# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
from collections import defaultdict
from django.core.management.base import BaseCommand
from django.conf import settings
from core.models import Rule, Flag, Person
from core.utils import expand_gdrive_download_url, download


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--infile",
            default=getattr(settings, "SCORING_FILE", ""),
            help="Link to json file to import",
        )

        parser.add_argument(
            "--force",
            default=False,
            action="store_true",
            help="Delete old flags and import new file despite all warnings",
        )

    def handle(self, *args, **kwargs):
        _, _, content = download(expand_gdrive_download_url(kwargs["infile"]))

        current_flags_count = Flag.objects.count()
        flags = []
        if content is None:
            self.stderr.write(
                "Cannot download file using url {}".format(kwargs["infile"])
            )

            return

        scores = defaultdict(float)

        for l in content.splitlines():
            d = json.loads(l)
            try:
                pep = Person.objects.get(pk=int(d.get("id_PEP", 0)))
                rule = Rule.objects.get(pk=d.get("Rule"))
            except Person.DoesNotExist:
                self.stderr.write("PEP with id '{}' doesn't exists".format(d.get("id_PEP")))
            except Rule.DoesNotExist:
                self.stderr.write("Rule with id '{}' doesn't exists".format(d.get("Rule")))

            scores[pep.pk] += rule.weight
            flags.append(Flag(
                person=pep,
                rule=rule,
                data=d.get("flag_data", {})
            ))

        if len(flags) < current_flags_count * 0.9 and not kwargs["force"]:
            self.stderr.write(
                "Major decrease in number of flags (was {}, now {}), aborting".format(
                    current_flags_count, len(flags)
                )
            )

            return

        Flag.objects.all().delete()
        Flag.objects.bulk_create(flags)

        max_score = max(scores.values())

        for pep_id, score in scores.items():
            if score == max_score:
                self.stdout.write("Max score is {} (pep {})".format(score, pep_id))
                break

        if max_score < 1. and not kwargs["force"]:
            self.stderr.write(
                "Max score is {} which is too low".format(
                    max_score
                )
            )

            return

        Rule.objects.update(scale=10 / max_score)
        self.stdout.write("Import is complete, {} new flags added".format(len(flags)))
