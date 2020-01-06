# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import os.path

from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from core.models import Document
from core.model.exc import WatermarkException

import PyPDF2
from tqdm import tqdm


class Command(BaseCommand):
    help = """
    Add watermarks to PDF documents
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "--category",
            help="Categories to use to tag documents",
            choices=Document.DOC_TYPE_CHOICES.keys(),
            nargs="+",
            default=Document.DOC_TYPE_TO_WATERMARK,
        )

        parser.add_argument(
            "--force", help="Rewrite watermarked", action="store_true", default=False
        )

    def handle(self, *args, **options):
        tagged_successfully = 0
        tagged_errors = 0

        qs = Document.objects.filter(doc_type__in=options["category"])
        for d in tqdm(qs.nocache().iterator(), total=qs.count()):
            try:
                res = d.generate_watermark(options["force"])
                if res:
                    tagged_successfully += 1
                elif res is None:
                    continue
                else:
                    tagged_errors += 1

            except WatermarkException as e:
                self.stderr.write(unicode(e))
                tagged_errors += 1

        self.stdout.write(
            "{} tagged tagged_successfully\n{} cannot be tagged".format(
                tagged_successfully, tagged_errors
            )
        )
