# coding: utf-8
from __future__ import unicode_literals

from django.db import models
from django.conf import settings
from django.core.urlresolvers import reverse
from django.forms.models import model_to_dict
from django.utils.translation import ugettext_lazy, activate, deactivate

from core.model.base import AbstractNode


class Country(models.Model, AbstractNode):
    name = models.CharField("Назва", max_length=100)
    iso2 = models.CharField("iso2 код", max_length=2, blank=True)
    iso3 = models.CharField("iso3 код", max_length=3, blank=True)
    is_jurisdiction = models.BooleanField("Не є країною", default=False)

    def __unicode__(self):
        return self.name

    @staticmethod
    def autocomplete_search_fields():
        return ("name_en__icontains", "name_uk__icontains")

    def get_absolute_url(self):
        return reverse("countries", kwargs={"country_id": self.iso2})

    def localized_url(self, locale):
        activate(locale)
        url = self.get_absolute_url()
        deactivate()
        return url

    @property
    def url_uk(self):
        return settings.SITE_URL + self.localized_url("uk")

    def get_node(self):
        res = super(Country, self).get_node()

        d = model_to_dict(
            self,
            fields=[
                "name_uk",
                "name_en",
                "iso2",
                "iso3",
                "is_jurisdiction",
                "url_uk",
                "url_en",
            ],
        )
        res["data"].update(d)

        del res["data"]["connections"]
        del res["data"]["description"]
        del res["data"]["kind"]
        del res["data"]["url"]
        del res["data"]["details"]

        return res

    class Meta:
        verbose_name = "Країна/юрісдикція"
        verbose_name_plural = "Країни/юрісдикції"

