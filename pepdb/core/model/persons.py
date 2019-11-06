# coding: utf-8
from __future__ import unicode_literals

from itertools import chain
from copy import deepcopy
from urlparse import urlparse
import datetime
from collections import defaultdict, OrderedDict

from django.db import models
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_noop as _
from django.utils.translation import ugettext_lazy, activate, get_language
from django.forms.models import model_to_dict
from django.conf import settings
from django.db.models.functions import Coalesce
from django.db.models import Q, Value, Max
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.fields import GenericRelation

from cacheops import cached
from translitua import translitua
import select2.fields
import select2.models
from dateutil.parser import parse as dt_parse

from core.fields import RedactorField
from core.model.base import AbstractNode
from core.model.translations import Ua2EnDictionary
from core.utils import (
    render_date,
    lookup_term,
    parse_fullname,
    translate_into,
    ceil_date,
)
from core.model.declarations import Declaration
from core.model.supplementaries import Document
from core.model.connections import Person2Person, Person2Company, Person2Country

# to_*_dict methods are used to convert two main entities that we have, Person
# and Company into document indexable by ElasticSearch.
# Links between Persons, Person and Company, Companies, Person and Country,
# Company and Country is also converted to subdocuments and attached to
# Person/Company documents. Because Person and Company needs different
# subdocuments, Person2Company has two different methods, to_person_dict and
# to_company_dict. For the same reason Person2Person and Company2Company has
# to_dict/to_dict_reverse because same link provides info to both persons.


class Person(models.Model, AbstractNode):
    _reasons_of_termination = (
        (1, _("Помер")),
        (2, _("Звільнився/склав повноваження")),
        (3, _("Пов'язана особа або член сім'ї - ПЕП помер")),
        (4, _("Пов'язана особа або член сім'ї - ПЕП припинив бути ПЕПом")),
        (5, _("Зміни у законодавстві що визначає статус ПЕПа")),
        (6, _("Зміни форми власності юр. особи посада в котрій давала статус ПЕПа")),
    )

    _types_of_officials = (
        (1, _("Національний публічний діяч")),
        (2, _("Іноземний публічний діяч")),
        (3, _("Діяч, що виконуює значні функції в міжнародній організації")),
        (4, _("Пов'язана особа")),
        (5, _("Член сім'ї")),
    )

    last_name = models.CharField("Прізвище", max_length=40)
    first_name = models.CharField("Ім'я", max_length=40)
    patronymic = models.CharField("По батькові", max_length=40, blank=True)

    publish = models.BooleanField("Опублікувати", default=True)
    is_pep = models.BooleanField("Є PEPом", default=True)
    imported = models.BooleanField("Був імпортований з гугл-таблиці", default=False)

    photo = models.ImageField("Світлина", blank=True, upload_to="images")
    dob = models.DateField("Дата народження", blank=True, null=True)
    dob_details = models.IntegerField(
        "Дата народження: точність",
        choices=((0, "Точна дата"), (1, "Рік та місяць"), (2, "Тільки рік")),
        default=0,
    )

    city_of_birth = models.CharField("Місто народження", max_length=100, blank=True)

    related_countries = models.ManyToManyField(
        "Country",
        verbose_name="Пов'язані країни",
        through="Person2Country",
        related_name="people",
    )

    reputation_assets = RedactorField("Статки", blank=True)

    reputation_sanctions = RedactorField("Наявність санкцій", blank=True)
    reputation_crimes = RedactorField("Кримінальні провадження", blank=True)
    reputation_manhunt = RedactorField("Перебування у розшуку", blank=True)
    reputation_convictions = RedactorField("Наявність судимості", blank=True)

    related_persons = select2.fields.ManyToManyField(
        "self",
        through="Person2Person",
        symmetrical=False,
        ajax=True,
        search_field=(lambda q: Q(last_name__icontains=q) | Q(first_name__icontains=q)),
    )

    related_companies = models.ManyToManyField("Company", through="Person2Company")

    wiki = RedactorField("Вікі-стаття", blank=True)
    wiki_draft = RedactorField("Чернетка вікі-статті", blank=True)

    wiki_url = models.URLField("Посилання на вікі", blank=True, max_length=1023)

    names = models.TextField("Варіанти написання імені", blank=True)

    also_known_as = models.TextField("Інші імена", blank=True)

    type_of_official = models.IntegerField(
        "Тип ПЕП", choices=_types_of_officials, blank=True, null=True
    )

    risk_category = models.CharField(
        "Рівень ризику",
        choices=(
            ("danger", _("Неприйнятно високий")),
            ("high", _("Високий")),
            ("medium", _("Середній")),
            ("low", _("Низький")),
        ),
        max_length=6,
        default="low",
    )

    title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)

    hash = models.CharField("Хеш", max_length=40, blank=True)

    reason_of_termination = models.IntegerField(
        "Причина припинення статусу ПЕП",
        choices=_reasons_of_termination,
        blank=True,
        null=True,
    )

    termination_date = models.DateField(
        "Дата припинення статусу ПЕП",
        blank=True,
        null=True,
        help_text="Вказується реальна дата зміни без врахування 3 років (реальна дата звільнення, тощо)",
    )
    termination_date_details = models.IntegerField(
        "Дата припинення статусу ПЕП: точність",
        choices=((0, "Точна дата"), (1, "Рік та місяць"), (2, "Тільки рік")),
        default=0,
    )

    last_change = models.DateTimeField(
        "Дата останньої зміни сторінки профіля", blank=True, null=True
    )

    last_editor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        verbose_name="Автор останньої зміни сторінки профілю",
        blank=True,
        null=True,
    )

    _last_modified = models.DateTimeField("Остання зміна", null=True, blank=True)

    inn = models.CharField(
        _("ІПН з публічних джерел"), max_length=40, null=True, blank=True
    )
    inn_source = models.ForeignKey(
        "core.Document",
        verbose_name="Документ з котрого було отримано ІПН",
        default=None,
        blank=True,
        null=True,
        related_name="inns",
    )
    passport = models.CharField(
        _("Паспортні дані з публічних джерел"), max_length=40, null=True, blank=True
    )
    passport_source = models.ForeignKey(
        "core.Document",
        verbose_name="Документ з котрого було отримано ІПН",
        default=None,
        blank=True,
        null=True,
        related_name="passports",
    )
    proofs = GenericRelation(
        "RelationshipProof", verbose_name="Посилання, соціальні мережі та документи"
    )

    @staticmethod
    def autocomplete_search_fields():
        return ("id__iexact", "last_name__icontains", "first_name__icontains")

    def __unicode__(self):
        return "%s %s %s" % (self.last_name, self.first_name, self.patronymic)

    @property
    def date_of_birth(self):
        return render_date(self.dob, self.dob_details)

    @property
    def termination_date_human(self):
        return render_date(self.termination_date, self.termination_date_details)

    @property
    def terminated(self):
        # (1, _("Помер")),
        # (2, _("Звільнився/склав повноваження")),
        # (3, _("Пов'язана особа або член сім'ї - ПЕП помер")),
        # (4, _("Пов'язана особа або член сім'ї - ПЕП припинив бути ПЕПом")),
        # (5, _("Зміни у законодавстві що визначає статус ПЕПа")),
        # (6, _("Зміни форми власності юр. особи посада в котрій давала статус ПЕПа")),

        if self.reason_of_termination in [1, 3]:
            return True

        if (
            self.reason_of_termination in [2, 4, 5, 6]
            and self.termination_date is not None
        ):
            if (
                ceil_date(self.termination_date, self.termination_date_details)
                + datetime.timedelta(days=3 * 365)
                <= datetime.date.today()
            ):
                return True

        return False

    @property
    def died(self):
        return self.reason_of_termination == 1

    def _last_workplace(self):
        # Looking for a most recent appointment that has at least one date set
        # It'll work in following three cases:
        # Case 1: date_finished=null, date_established is the most recent one
        # i.e person got appointed and still holds the office
        # else
        # Case 2: date_finished=is the most recent one
        # and the date_established is the most recent one or null
        # i.e person got appointed and then resigned.

        # Tricky part: null values in dates are getting on top of the list when
        # you are sorting in decreasing order. So without exclude clause this
        # query will return the positions without both dates on the top of the
        # list
        qs = (
            self.person2company_set.order_by(
                "-is_employee", "-date_finished", "-date_established"
            )
            .exclude(date_finished__isnull=True, date_established__isnull=True)  # AND!
            .exclude(relationship_type_uk="Клієнт банку")
            .prefetch_related("to_company")
            .only(
                "to_company__short_name_uk",
                "to_company__name_uk",
                "to_company__short_name_en",
                "to_company__name_en",
                "to_company__id",
                "relationship_type_uk",
                "relationship_type_en",
                "date_finished",
                "date_finished_details",
                "from_person_id",
                "id",
            )
        )

        if qs:
            return qs

        # If nothing is found we are going to return the position that
        # has finished date set to null or the most recent one.
        # In contrast with previous query it'll also return those positions
        # where date_finished and date_established == null.
        qs = (
            self.person2company_set.order_by("-is_employee", "-date_finished")
            .prefetch_related("to_company")
            .exclude(relationship_type_uk="Клієнт банку")
            .only(
                "to_company__short_name_uk",
                "to_company__name_uk",
                "to_company__short_name_en",
                "to_company__name_en",
                "to_company__id",
                "relationship_type_uk",
                "relationship_type_en",
                "date_finished",
                "date_finished_details",
                "from_person_id",
                "id",
            )
        )

        return qs

    @property
    def day_of_dismissal(self):
        dday = self._last_workplace().filter(is_employee=True).first()
        if dday:
            return render_date(dday.date_finished, dday.date_finished_details)
        else:
            return False

    def _last_workplace_from_declaration(self):
        return (
            Declaration.objects.filter(person=self, confirmed="a")
            .exclude(doc_type="Кандидата на посаду")
            .order_by("-nacp_declaration", "-year")
            .only(
                "year", "office_en", "position_en", "office_uk", "position_uk", "url"
            )[:1]
        )

    @property
    def last_workplace(self):
        qs = self._last_workplace()
        if qs:
            l = qs[0]
            return {
                "company": l.to_company.short_name_uk or l.to_company.name_uk,
                "company_id": l.to_company.pk,
                "position": l.relationship_type_uk,
            }
        else:
            qs = self._last_workplace_from_declaration()
            if qs:
                d = qs[0]
                return {
                    "company": d.office_uk,
                    "company_id": None,
                    "position": d.position_uk,
                }

        return ""

    # Fuuugly hack
    @property
    def last_workplace_en(self):
        qs = self._last_workplace()
        if qs:
            l = qs[0]

            return {
                "company": l.to_company.short_name_en or l.to_company.name_en,
                "company_id": l.to_company.pk,
                "position": l.relationship_type_en,
            }
        else:
            qs = self._last_workplace_from_declaration()
            if qs:
                d = qs[0]
                return {
                    "company": d.office_en,
                    "company_id": None,
                    "position": d.position_en,
                }

        return ""

    # Fuuugly hack
    @property
    def translated_last_workplace(self):
        # Add caching
        qs = self._last_workplace()
        if qs:
            l = qs[0]

            return {
                "company": l.to_company.short_name or l.to_company.name,
                "company_id": l.to_company.pk,
                "position": l.relationship_type,
            }
        else:
            qs = self._last_workplace_from_declaration()
            if qs:
                d = qs[0]
                return {"company": d.office, "company_id": None, "position": d.position}

        return ""

    @property
    def workplaces(self):
        # Coalesce works by taking the first non-null value.  So we give it
        # a date far before any non-null values of last_active.  Then it will
        # naturally sort behind instances of Box with a non-null last_active
        # value.
        # djangoproject.com/en/1.8/ref/models/database-functions/#coalesce
        the_past = datetime.datetime.now() - datetime.timedelta(days=10 * 365)

        timeline = (
            self.person2company_set.prefetch_related(
                "to_company", "proofs", "proofs__proof_document"
            )
            .filter(is_employee=True)
            .annotate(
                fixed_date_established=Coalesce("date_established", Value(the_past))
            )
            .order_by("-fixed_date_established")
        )

        return timeline

    @property
    def assets(self):
        return self.person2company_set.prefetch_related(
            "to_company", "proofs", "proofs__proof_document"
        ).filter(
            is_employee=False,
            relationship_type_uk__in=(
                "Член центрального статутного органу",
                "Повірений у справах",
                "Засновник/учасник",
                "Колишній засновник/учасник",
                "Бенефіціарний власник",
                "Номінальний власник",
                "Номінальний директор",
                "Фінансові зв'язки",
                "Секретар",
                "Керуючий",
                "Контролер",
            ),
        )

    @property
    def all_related_companies(self):
        companies = (
            self.person2company_set.prefetch_related(
                "to_company", "proofs", "proofs__proof_document"
            )
            .filter(is_employee=False)
            .order_by("-pk")
        )

        banks = []
        rest = []
        all_connections = []
        for c in companies:
            if c.relationship_type_uk == "Клієнт банку":
                banks.append(c)
            else:
                rest.append(c)

            all_connections.append(c)

        return {"banks": banks, "rest": rest, "all": all_connections}

    @property
    def all_related_persons(self):
        related_persons = [
            (i.to_relationship_type, i.from_relationship_type, deepcopy(i.to_person), i)
            for i in self.to_persons.prefetch_related(
                "to_person", "proofs", "proofs__proof_document"
            ).defer(
                "to_person__reputation_assets",
                "to_person__reputation_sanctions",
                "to_person__reputation_crimes",
                "to_person__reputation_manhunt",
                "to_person__reputation_convictions",
                "to_person__wiki",
                "to_person__names",
                "to_person__hash",
            )
        ] + [
            (
                i.from_relationship_type,
                i.to_relationship_type,
                deepcopy(i.from_person),
                i,
            )
            for i in self.from_persons.prefetch_related(
                "from_person", "proofs", "proofs__proof_document"
            ).defer(
                "from_person__reputation_assets",
                "from_person__reputation_sanctions",
                "from_person__reputation_crimes",
                "from_person__reputation_manhunt",
                "from_person__reputation_convictions",
                "from_person__wiki",
                "from_person__names",
                "from_person__hash",
            )
        ]

        res = {"family": [], "personal": [], "business": [], "all": []}

        for rtp, rrtp, p, rel in related_persons:
            p.rtype = rtp
            p.reverse_rtype = rrtp
            p.connection = rel

            if rtp in ["особисті зв'язки"]:
                res["personal"].append(p)
            elif rtp in ["ділові зв'язки"]:
                res["business"].append(p)
            else:
                res["family"].append(p)

            res["all"].append(p)

        return res

    @property
    def parsed_names(self):
        return filter(None, self.names.split("\n"))

    @property
    def full_name(self):
        return (
            "%s %s %s" % (self.first_name, self.patronymic, self.last_name)
        ).replace("  ", " ").strip()


    @property
    def short_name(self):
        return (
            "%s %s" % (self.first_name, self.last_name)
        ).replace("  ", " ").strip()


    @property
    def full_name_en(self):
        return (
            "%s %s %s" % (self.first_name_en, self.patronymic_en, self.last_name_en)
        ).replace("  ", " ")

    def to_dict(self):
        """
        Convert Person model to an indexable presentation for ES.
        """
        d = model_to_dict(
            self,
            fields=[
                "id",
                "last_name",
                "first_name",
                "patronymic",
                "dob",
                "last_name_en",
                "first_name_en",
                "patronymic_en",
                "dob_details",
                "is_pep",
                "names",
                "wiki_uk",
                "wiki_en",
                "city_of_birth_uk",
                "city_of_birth_en",
                "reputation_sanctions_uk",
                "reputation_sanctions_en",
                "reputation_convictions_uk",
                "reputation_convictions_en",
                "reputation_assets_uk",
                "reputation_assets_en",
                "reputation_crimes_uk",
                "reputation_crimes_en",
                "reputation_manhunt_uk",
                "reputation_manhunt_en",
                "also_known_as_uk",
                "also_known_as_en",
                "last_change",
                "inn",
                "inn_source",
                "passport",
                "passport_source",
            ],
        )

        d["related_persons"] = [
            i.to_dict() for i in self.to_persons.prefetch_related("to_person")
        ] + [
            i.to_dict_reverse()
            for i in self.from_persons.prefetch_related("from_person")
        ]
        d["related_countries"] = [
            i.to_dict() for i in self.person2country_set.prefetch_related("to_country")
        ]
        d["related_companies"] = [
            i.to_company_dict()
            for i in self.person2company_set.prefetch_related("to_company")
        ]

        d["declarations"] = [
            i.to_dict() for i in Declaration.objects.filter(person=self, confirmed="a")
        ]

        manhunt_records = self.manhunt_records
        if manhunt_records:
            curr_lang = get_language()

            activate("uk")
            d["reputation_manhunt_uk"] = render_to_string(
                "_manhunt_records_uk.jinja", {"manhunt_records": manhunt_records}
            ) + (d["reputation_manhunt_uk"] or "")

            activate("en")
            d["reputation_manhunt_en"] = render_to_string(
                "_manhunt_records_en.jinja", {"manhunt_records": manhunt_records}
            ) + (d["reputation_manhunt_en"] or "")
            activate(curr_lang)

        d["inn_source"] = (
            settings.SITE_URL + self.inn_source.doc.url if self.inn_source else ""
        )
        d["passport_source"] = (
            settings.SITE_URL + self.passport_source.doc.url
            if self.passport_source
            else ""
        )

        d["photo"] = settings.SITE_URL + self.photo.url if self.photo else ""
        d["photo_path"] = self.photo.name if self.photo else ""
        d["date_of_birth"] = self.date_of_birth
        d["terminated"] = self.terminated
        d["last_modified"] = self.last_modified
        d["died"] = self.died
        if d["terminated"]:
            d["reason_of_termination"] = self.get_reason_of_termination_display()
            d["reason_of_termination_en"] = translate_into(
                self.get_reason_of_termination_display(), "en"
            )
            d["termination_date_human"] = self.termination_date_human

        last_workplace = self.last_workplace
        if last_workplace:
            d["last_workplace"] = last_workplace["company"]
            d["last_job_title"] = last_workplace["position"]
            d["last_job_id"] = last_workplace["company_id"]

            last_workplace_en = self.last_workplace_en
            d["last_workplace_en"] = last_workplace_en["company"]
            d["last_job_title_en"] = last_workplace_en["position"]

        d["type_of_official"] = self.get_type_of_official_display()

        d["type_of_official_en"] = translate_into(
            self.get_type_of_official_display(), "en"
        )

        d["full_name"] = self.full_name
        d["full_name_en"] = self.full_name_en

        def generate_suggestions(last_name, first_name, patronymic, *args):
            if not last_name:
                return []

            return [
                {"input": " ".join([last_name, first_name, patronymic]), "weight": 5},
                {"input": " ".join([first_name, patronymic, last_name]), "weight": 2},
                {"input": " ".join([first_name, last_name]), "weight": 2},
            ]

        input_variants = [
            generate_suggestions(d["last_name"], d["first_name"], d["patronymic"])
        ]

        input_variants += list(
            map(lambda x: generate_suggestions(*parse_fullname(x)), self.parsed_names)
        )

        d["full_name_suggest"] = list(chain.from_iterable(input_variants))

        d["_id"] = d["id"]

        return d

    def get_absolute_url(self):
        return reverse("person_details", kwargs={"person_id": self.pk})

    def localized_url(self, locale):
        curr_lang = get_language()
        activate(locale)
        url = self.get_absolute_url()
        activate(curr_lang)
        return url

    @property
    def foreign_citizenship_or_registration(self):
        return self.person2country_set.prefetch_related("to_country").filter(
            relationship_type__in=["citizenship", "registered_in"]
        )

    @property
    def foreign_citizenship(self):
        return self.person2country_set.prefetch_related("to_country").filter(
            relationship_type="citizenship"
        )

    @property
    def url_uk(self):
        return settings.SITE_URL + self.localized_url("uk")

    def save(self, *args, **kwargs):
        if self.first_name_uk:
            self.first_name_en = self.first_name_en or translitua(self.first_name_uk)
        else:
            self.first_name_en = ""

        if self.last_name_uk:
            self.last_name_en = self.last_name_en or translitua(self.last_name_uk)
        else:
            self.last_name_en = ""

        if self.patronymic_uk:
            self.patronymic_en = self.patronymic_en or translitua(self.patronymic_uk)
        else:
            self.patronymic_en = ""

        if self.also_known_as_uk:
            self.also_known_as_en = translitua(self.also_known_as_uk)
        else:
            self.also_known_as_en = ""

        if self.city_of_birth_uk and not self.city_of_birth_en:
            t = Ua2EnDictionary.objects.filter(
                term__iexact=lookup_term(self.city_of_birth_uk)
            ).first()

            if t and t.translation:
                self.city_of_birth_en = t.translation

        super(Person, self).save(*args, **kwargs)

    @cached(timeout=60 * 2)
    def get_declarations(self):
        decls = Declaration.objects.filter(person=self, confirmed="a").order_by(
            "-year", "-nacp_declaration"
        )

        corrected = []
        res = []
        # Filtering out original declarations, if there are
        # also corrected one
        for d in decls:
            if not d.nacp_declaration:
                continue

            if d.source["intro"].get("corrected"):
                corrected.append((d.year, d.source["intro"].get("doc_type")))

        for d in decls:
            if d.nacp_declaration and not d.source["intro"].get("corrected"):
                if (d.year, d.source["intro"].get("doc_type")) in corrected:
                    continue

            res.append(d)

        return res

    def get_charts_data(self):
        def cleanse(val):
            try:
                return float(unicode(val))
            except ValueError:
                return None

        decls = self.get_declarations()

        incomes = [
            [
                unicode(ugettext_lazy('Рік')),
                unicode(ugettext_lazy('Доходи декларанта')),
                unicode(ugettext_lazy('Доходи родини')),
                unicode(ugettext_lazy('Витрати декларанта'))
            ],
        ]

        assets = [
            [
                unicode(ugettext_lazy('Рік')),
                unicode(ugettext_lazy('Декларант')),
                unicode(ugettext_lazy('Родина'))
            ]
        ]

        for d in decls[::-1]:
            income = d.get_income()
            incomes.append([
                unicode(income["year"]),
                cleanse(income["income_of_declarant"]),
                cleanse(income["income_of_family"]),
                cleanse(income["expenses_of_declarant"]),
            ])

            asset = d.get_assets()
            assets.append([
                unicode(asset["year"]),
                cleanse(asset["total_uah"]["declarant"]),
                cleanse(asset["total_uah"]["family"])
            ])

        return {
            "incomes": incomes,
            "assets": assets,
        }

    def get_node(self):
        res = super(Person, self).get_node()

        node = {
            "is_pep": self.is_pep,
            "type_of_official": self.type_of_official or 0,
            "reason_of_termination": self.reason_of_termination or 0,
            "is_dead": self.reason_of_termination in [1, 3],
        }

        curr_lang = get_language()
        for lang in settings.LANGUAGE_CODES:
            activate(lang)
            node.update({
                "name_{}".format(lang): self.short_name,
                "full_name_{}".format(lang): self.full_name,
                "kind_{}".format(lang): unicode(ugettext_lazy(self.get_type_of_official_display() or ""))
            })

            last_workplace = self.translated_last_workplace
            if last_workplace:
                last_workplace = "{position} @ {company}".format(**last_workplace)
            else:
                last_workplace = ""

            node["description_{}".format(lang)] = last_workplace

        activate(curr_lang)
        res["data"].update(node)
        del res["data"]["connections"]
        del res["data"]["description"]
        del res["data"]["kind"]
        del res["data"]["url"]
        del res["data"]["id"]
        del res["data"]["details"]

        return res

    # temporary hack to keep old viz afloat
    def get_node_old(self):
        res = super(Person, self).get_node()

        node = {
            "name": self.short_name,
            "full_name": self.full_name,
            "is_pep": self.is_pep,
            "type_of_official": self.type_of_official,
            "reason_of_termination": self.reason_of_termination,
            "is_dead": self.reason_of_termination in [1, 3],
            "kind": unicode(ugettext_lazy(self.get_type_of_official_display() or ""))
        }
        last_workplace = self.translated_last_workplace

        if last_workplace:
            node["description"] = "{position} @ {company}".format(**last_workplace)

        res["data"].update(node)

        return res

    def get_node_info(self, with_connections=False):
        this_node = self.get_node_old()
        nodes = [this_node]
        edges = []
        all_connected = set()

        # Because of a complicated logic here we are piggybacking on
        # existing method that handles both directions of relations
        for p in self.all_related_persons["all"]:
            child_node_id = p.get_node_id()

            if with_connections:
                child_node = p.get_node_info(False)

                nodes += child_node["nodes"]
                edges += child_node["edges"]

                edges.append(
                    {
                        "data": {
                            "relation": unicode(ugettext_lazy(p.rtype)),
                            "model": p.connection._meta.model_name,
                            "pk": p.connection.pk,
                            "id": "{}-{}".format(
                                p.connection._meta.model_name, p.connection.pk
                            ),
                            "share": 0,
                            "source": this_node["data"]["id"],
                            "target": child_node_id,
                            "is_latest": True
                        }
                    }
                )

            all_connected.add(child_node_id)

        companies = self.person2company_set.prefetch_related("to_company").exclude(relationship_type_uk="Клієнт банку")

        worked_for = {}
        connected_to = {}

        if with_connections:
            for c in companies:
                c.is_latest = False

                child_node_id = c.to_company.get_node_id()

                if c.is_employee:
                    bucket = worked_for
                else:
                    bucket = connected_to

                if child_node_id not in bucket:
                    bucket[child_node_id] = c
                else:
                    compare_with = bucket[child_node_id]

                    # When comparing two connections
                    if c.date_finished is not None or c.date_established is not None:
                        # Candidate with date_finished and date_established not set looses
                        if compare_with.date_finished is None and compare_with.date_established is None:
                            bucket[child_node_id] = c
                        else:
                            dt_now = (datetime.datetime.now() + datetime.timedelta(days=7)).date()

                            a_date_established = compare_with.date_established or dt_now
                            b_date_established = c.date_established or dt_now

                            a_date_finished = compare_with.date_finished or dt_now
                            b_date_finished = c.date_finished or dt_now

                            # Candidate with later date finished or open date_finished wins
                            if b_date_finished > a_date_finished:
                                bucket[child_node_id] = c
                            elif b_date_finished == a_date_finished:
                                # if both date finished are the same (for example two connections has open end)
                                # those with latest date_established wins
                                if b_date_established > a_date_established:
                                    bucket[child_node_id] = c


            for bucket in [worked_for, connected_to]:
                for c in bucket.values():
                    c.is_latest = True

        for c in companies:
            child_node_id = c.to_company.get_node_id()

            if with_connections:
                child_node = c.to_company.get_node_info(False)
                nodes += child_node["nodes"]
                edges += child_node["edges"]

                edges.append(
                    {
                        "data": {
                            "relation": unicode(c.relationship_type),
                            "model": c._meta.model_name,
                            "pk": c.pk,
                            "id": "{}-{}".format(
                                c._meta.model_name, c.pk
                            ),
                            "source": this_node["data"]["id"],
                            "share": float(c.share or 0),
                            "target": child_node_id,
                            "is_latest": c.is_latest
                        }
                    }
                )

            all_connected.add(child_node_id)

        this_node["data"]["all_connected"] = list(all_connected)
        return {"edges": edges, "nodes": nodes}

    @property
    def manhunt_records(self):
        return [
            {
                "last_updated_from_dataset": rec.last_updated_from_dataset,
                "lost_date": dt_parse(rec.matched_json["LOST_DATE"], yearfirst=True),
                "articles_uk": rec.matched_json["ARTICLE_CRIM"],
                "articles_en": rec.matched_json["ARTICLE_CRIM"]
                .lower()
                .replace("ст.", "article ")
                .replace("ч.", "pt. "),
            }
            for rec in self.adhoc_matches.filter(status="a", dataset_id="wanted_ia")
        ]

    @property
    def last_modified(self):
        p2p_conn = Person2Person.objects.filter(
            Q(from_person=self) | Q(to_person=self)
        ).aggregate(mm=Max("_last_modified"))["mm"]

        p2comp_conn = Person2Company.objects.filter(Q(from_person=self)).aggregate(
            mm=Max("_last_modified")
        )["mm"]

        p2cont_conn = Person2Country.objects.filter(Q(from_person=self)).aggregate(
            mm=Max("_last_modified")
        )["mm"]

        seq = list(
            filter(
                None,
                [
                    p2p_conn,
                    p2comp_conn,
                    p2cont_conn,
                    self.last_change,
                    self._last_modified,
                ],
            )
        )
        if seq:
            return max(seq)

    @property
    def external_links(self):
        social_networks = {
            "facebook.com": "Facebook",
            "twitter.com": "Twitter",
            "vk.com": "Vkontakte",
            "instagram.com": "Instagram",
            "ok.ru": "Odnoklassniki",
            "linkedin.com": "LinkedIn"
        }
        other_networks = {
            "ru.wikipedia.org": "Wikipedia",
            "en.wikipedia.org": "Wikipedia",
            "de.wikipedia.org": "Wikipedia",
            "uk.wikipedia.org": "Wikipedia",
        }

        res = {
            "social_networks": [],
            "other": []
        }

        for proof in self.proofs.all():
            if proof.proof:
                domain = urlparse(proof.proof).hostname
                if domain is None:
                    continue
                
                domain = domain.replace("www.", "").lower()

                if domain in social_networks:
                    res["social_networks"].append({
                        "type": social_networks[domain],
                        "title": social_networks[domain],
                        "url": proof.proof
                    })
                else:
                    res["other"].append({
                        "type": domain,
                        "title": proof.proof_title or other_networks.get(domain, domain),
                        "url": proof.proof
                    })

        return res

    def clean(self):
        if self.inn is not None and self.inn_source is None:
            raise ValidationError(
                {
                    "inn": "Не можна вказувати ІПН не надавши документальне підтвердження",
                    "inn_source": "Не можна вказувати ІПН не надавши документальне підтвердження",
                }
            )

        if self.passport is not None and self.passport_source is None:
            raise ValidationError(
                {
                    "passport": "Не можна вказувати ІПН не надавши документальне підтвердження",
                    "passport_source": "Не можна вказувати ІПН не надавши документальне підтвердження",
                }
            )

    @property
    def all_documents(self):
        companies = self.all_related_companies
        persons = self.all_related_persons
        proofs = []
        proofs_by_cat = defaultdict(list)

        for p in persons["all"]:
            for proof in p.connection.proofs.all():
                if not proof.proof_document:
                    continue
                proofs.append(proof)

        for c in companies["all"]:
            for proof in c.proofs.all():
                if not proof.proof_document:
                    continue
                proofs.append(proof)

        seen = set()
        for proof in proofs + list(self.proofs.all()):
            if proof.proof_document_id not in seen:
                if not proof.proof_document:
                    continue

                proofs_by_cat[proof.proof_document.doc_type].append(
                    proof
                )

                seen.add(proof.proof_document_id)

        proofs_by_cat["misc"] += proofs_by_cat["other"]
        del proofs_by_cat["other"]

        return OrderedDict(
            (Document.DOC_TYPE_CHOICES[k], proofs_by_cat[k]) for k in Document.DOC_TYPE_CHOICES.keys()
        )


    class Meta:
        verbose_name = "Фізична особа"
        verbose_name_plural = "Фізичні особи"

        index_together = [["last_name", "first_name"]]

        permissions = (
            ("export_persons", "Can export the dataset"),
            (
                "export_id_and_last_modified",
                "Can export the dataset with person id and date of last modification",
            ),
        )
