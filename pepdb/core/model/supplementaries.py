# coding: utf-8
from __future__ import unicode_literals
import re
import os.path
from collections import OrderedDict
from glob import glob
from io import BytesIO
import random

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy
from django.core.files.base import File

import PyPDF2

from core.model.exc import WatermarkException


WATERMARKS = {}
for f in glob(settings.WATERMARKS_PATH):
    name, _ = os.path.splitext(os.path.basename(f))

    WATERMARKS[name] = PyPDF2.PdfFileReader(open(f, "rb")).getPage(0)


class Document(models.Model):
    DOC_TYPE_CHOICES = OrderedDict(
        (
            ("business_registry", ugettext_lazy("Виписки з реєстру компаній")),
            ("court_decision", ugettext_lazy("Рішення суду")),
            ("declarations", ugettext_lazy("Декларації")),
            ("real_estate_registry", ugettext_lazy("Виписки з реєстру нерухомості")),
            ("order_to_dismiss", ugettext_lazy("Накази про звільнення")),
            ("media", ugettext_lazy("Публікація в медіа")),
            ("decree", ugettext_lazy("Рішення")),
            ("report", ugettext_lazy("Звіти")),
            ("ownership_structure", ugettext_lazy("Структури власності")),
            ("misc", ugettext_lazy("Інші документи")),
            ("other", ugettext_lazy("Неможливо ідентифікувати")),
        )
    )

    DOC_TYPE_TO_WATERMARK = [
        "misc",
        "other",
        "business_registry",
        "court_decision",
        "real_estate_registry",
        "order_to_dismiss",
        "decree",
        "report",
        "ownership_structure",
    ]

    doc = models.FileField("Файл", upload_to="documents", max_length=1000)
    doc_watermarked = models.FileField(
        "Файл з водяним знаком", upload_to="documents/_", max_length=1000, blank=True
    )
    name = models.CharField("Людська назва", max_length=255)
    uploaded = models.DateTimeField("Був завантажений", auto_now=True)
    source = models.CharField("Першоджерело", blank=True, max_length=255)
    uploader = models.ForeignKey(
        User, verbose_name="Хто завантажив", related_name="pep_document"
    )
    hash = models.CharField("Хеш", max_length=40, blank=True)
    comments = models.TextField("Коментарі", blank=True)
    doc_type = models.CharField(
        "Тип документу",
        max_length=25,
        choices=DOC_TYPE_CHOICES.items(),
        default="other",
    )
    doc_type_set_manually = models.BooleanField(
        "Тип документу був встановлений вручну", default=False
    )

    @staticmethod
    def autocomplete_search_fields():
        return ("id__iexact", "name__icontains", "source__icontains")

    @property
    def doc_url(self):
        if self.doc_watermarked:
            return self.doc_watermarked.url
        else:
            return self.doc.url
    

    def guess_doc_type(self, force=False):
        if not force and self.doc_type_set_manually:
            return

        outcome = "other"
        filename = self.doc.name
        PATTERNS = {
            r"business?[-_\s]r?egistry": "business_registry",
            r"court[-_\s]decision": "court_decision",
            r"declaration": "declarations",
            r"real[-_\s]property": "real_estate_registry",
            r"property[-_\s]registry": "real_estate_registry",
            r"land[-_\s]registry": "real_estate_registry",
            r"real[-_\s]estate[-_\s]registry": "real_estate_registry",
            r"order[-_\s]to[-_\s]dismiss": "order_to_dismiss",
            r"звільнення": "order_to_dismiss",
            r"decree": "decree",
            r"report": "report",
            r"raport": "report",
            r"ownership[-_\s]structure": "ownership_structure",
        }

        for r, dtype in PATTERNS.items():
            if re.search(r, filename, flags=re.I):
                outcome = dtype
                break

        if outcome == "other":
            if "_" in filename:
                prefix, _ = filename.split("_", 1)

                m = re.search(r"\.(\w+)$", prefix)
                if m:
                    tld = m.group(1).lower()
                    if tld in ["ua", "com", "org", "info", "eu", "net", "tv"]:
                        outcome = "media"

        self.doc_type = outcome
        self.save()

    def generate_watermark(self, force=False):
        fname, ext = os.path.splitext(self.doc.name)

        if self.doc_type not in self.DOC_TYPE_TO_WATERMARK:
            return None

        if self.doc_watermarked:
            if not force:
                return None
            else:
                self.doc_watermarked.delete()

        watermark = WATERMARKS["a4_portrait"]
        watermark_box = watermark.artBox
        watermark_w = float(watermark_box[2] - watermark_box[0])
        watermark_h = float(watermark_box[3] - watermark_box[1])

        if ext.lower() == ".pdf":
            try:
                curr_file = PyPDF2.PdfFileReader(self.doc.file, strict=False)
                pdf_writer = PyPDF2.PdfFileWriter()
                for page_no in range(curr_file.getNumPages()):
                    curr_page = curr_file.getPage(page_no)
                    file_box = curr_page.artBox
                    file_w = float(file_box[2] - file_box[0])
                    file_h = float(file_box[3] - file_box[1])

                    scale = min(
                        file_w / (watermark_w + 0.01), file_h / (watermark_h + 0.01)
                    )
                    curr_page.mergeScaledPage(watermark, scale, expand=True)
                    pdf_writer.addPage(curr_page)
            except IOError as e:
                raise WatermarkException(
                    "Cannot find file {}, skipping".format(self.doc.name)
                )
            except (PyPDF2.utils.PdfReadError, ValueError, OSError) as e:
                raise WatermarkException(
                    "Cannot read file {}, error was {}".format(self.doc.name, e)
                )

            with BytesIO() as fp:
                pdf_writer.write(fp)
                random.seed(self.pk)
                self.doc_watermarked.save(
                    "{}_{}_{}.pdf".format(
                        random.randrange(1000, 10000),
                        os.path.basename(fname),
                        random.randrange(1000, 10000),
                    ),
                    File(fp),
                )
        else:
            return False

        return True

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = "Документ"
        verbose_name_plural = "Документи"


class FeedbackMessage(models.Model):
    person = models.CharField(ugettext_lazy("Про кого"), max_length=150, blank=True)
    text = models.TextField(ugettext_lazy("Інформація"), blank=False)
    link = models.URLField(ugettext_lazy("Підтвердження"), max_length=512, blank=True)
    email = models.EmailField(ugettext_lazy("e-mail"), max_length=512, blank=True)
    contacts = models.TextField(
        ugettext_lazy("Ваше ім'я та контакти"), max_length=512, blank=True
    )
    read = models.BooleanField(ugettext_lazy("Прочитано"), default=False)
    added = models.DateTimeField("Був надісланий", auto_now=True)

    answered_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, verbose_name="Відповів", blank=True, null=True
    )
    answer_added = models.DateTimeField("Була надіслана", blank=True, null=True)
    short_answer = models.TextField("Суть відповіді", blank=True, null=True)
    read_and_agreed = models.BooleanField(
        "Користувач підтвердив що прочитав часто задаваємі питання", default=False
    )

    class Meta:
        verbose_name = "Зворотній зв'язок"
        verbose_name_plural = "Зворотній зв'язок"


class ActionLog(models.Model):
    user = models.ForeignKey(User, verbose_name="Користувач")
    action = models.CharField(verbose_name="Дія", max_length=30)
    timestamp = models.DateTimeField(verbose_name="Дата та час", auto_now_add=True)
    details = models.TextField(verbose_name="Деталі", blank=True)

    class Meta:
        verbose_name = "Дія користувача"
        verbose_name_plural = "Дії користувачів"

        index_together = [["user", "action", "timestamp"]]
