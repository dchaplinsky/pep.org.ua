# coding: utf-8
from __future__ import unicode_literals
from django.db import models
from django.utils.translation import ugettext_noop as _
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.auth.models import User

import select2.fields
from core.fields import RedactorField


class Article(models.Model):
    ARTICLE_KINDS = {"b": _("блог"), "i": _("розслідування")}

    photo = models.ImageField("Головна світлина", blank=True, upload_to="images")

    caption = models.TextField("Заголовок")
    header = models.TextField("Піздаголовок", blank=True)
    text = RedactorField("Текст", blank=True)

    publish = models.BooleanField("Опубліковано", default=False)
    date = models.DateField("Дата публікації")
    kind = models.CharField(
        "Тип статті", max_length=5, default="b", choices=ARTICLE_KINDS.items()
    )
    proofs = GenericRelation(
        "RelationshipProof", verbose_name="Посилання, соціальні мережі та документи"
    )

    related_persons = models.ManyToManyField("Person", verbose_name="Пов'язані особи")
    related_companies = models.ManyToManyField(
        "Company", verbose_name="Пов'язані компанії"
    )

    last_editor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        verbose_name="Автор останньої зміни",
        blank=True,
        null=True,
    )

    last_modified = models.DateTimeField("Остання зміна", auto_now=True)

    def __unicode__(self):
        return '{} ({})'.format(self.caption_uk, self.get_kind_display())

    class Meta:
        verbose_name = "Стаття"
        verbose_name_plural = "Статті"
