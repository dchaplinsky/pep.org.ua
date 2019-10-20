# coding: utf-8
from __future__ import unicode_literals

from django.db import models
from django.core.urlresolvers import reverse
from django.contrib.contenttypes.fields import GenericRelation

from core.utils import render_date


class AbstractNode(object):
    def get_model_name(self):
        t = type(self)
        if t is models.DEFERRED:
            t = t.__base__

        return t._meta.model_name

    def get_node_id(self):
        return "{}-{}".format(self.get_model_name(), self.pk)

    def get_node(self):
        model_name = self.get_model_name()

        return {
            "data": {
                "id": self.get_node_id(),
                "pk": self.pk,
                "url": self.get_absolute_url(),
                "model": model_name,
                "details": reverse(
                    "connections", kwargs={"model": model_name, "obj_id": self.pk}
                ),
                "kind": "",
                "description": "",
                "connections": [],
            }
        }


class AbstractRelationship(models.Model):
    date_established = models.DateField("Зв'язок почався", blank=True, null=True)

    date_established_details = models.IntegerField(
        "точність",
        choices=((0, "Точна дата"), (1, "Рік та місяць"), (2, "Тільки рік")),
        default=0,
    )

    date_finished = models.DateField("Зв'язок скінчився", blank=True, null=True)

    date_finished_details = models.IntegerField(
        "точність",
        choices=((0, "Точна дата"), (1, "Рік та місяць"), (2, "Тільки рік")),
        default=0,
    )

    date_confirmed = models.DateField("Підтверджено", blank=True, null=True)

    date_confirmed_details = models.IntegerField(
        "точність",
        choices=((0, "Точна дата"), (1, "Рік та місяць"), (2, "Тільки рік")),
        default=0,
    )

    @property
    def date_established_human(self):
        return render_date(self.date_established, self.date_established_details)

    @property
    def date_finished_human(self):
        return render_date(self.date_finished, self.date_finished_details)

    @property
    def date_confirmed_human(self):
        return render_date(self.date_confirmed, self.date_confirmed_details)

    proofs = GenericRelation("RelationshipProof")

    proof_title = models.TextField(
        "Назва доказу зв'язку",
        blank=True,
        help_text="Наприклад: склад ВР 7-го скликання",
    )
    proof = models.TextField("Посилання на доказ зв'язку", blank=True)

    @property
    def has_additional_info(self):
        if any([self.date_confirmed, self.date_established, self.date_finished]):
            return True

        return bool(self.proofs.count())

    _last_modified = models.DateTimeField("Остання зміна", null=True, blank=True)

    class Meta:
        abstract = True
