# coding: utf-8
from __future__ import unicode_literals
import re
from copy import copy, deepcopy
from datetime import date
from collections import defaultdict, OrderedDict

from django.db import models
from django.contrib.auth.models import User
from django.db.models import Q, Max
from django.core.urlresolvers import reverse
from django.conf import settings
from django.utils.translation import ugettext_noop as _
from django.utils.translation import ugettext_lazy, activate, get_language
from django.forms.models import model_to_dict
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.contenttypes.fields import GenericRelation

from core.fields import RedactorField

from core.model.base import AbstractNode
from core.model.translations import Ua2EnDictionary
from core.utils import render_date, lookup_term, translate_into, ceil_date
from core.model.supplementaries import Document
from core.model.connections import Company2Company, Company2Country, Person2Company


class CompanyManager(models.Manager):
    def deep_get(self, clauses):
        """
        Two-stage search which takes into account company status
        """

        query = Q()
        for field, value in clauses:

            if value:
                if len(value) < 2:
                    continue

                query |= Q(**{field: value})

        try:
            # Sometime in companies table we have more than one company
            # with same code, that usually happens when company got
            # reorganized or resurrected or something else strange had
            # happened

            # Here we'll try to update the most record of the company
            # in business first by narrowing down the search by using
            # status field
            return self.get(query & Q(status=1))
        except ObjectDoesNotExist:
            return self.get(query)


# to_*_dict methods are used to convert two main entities that we have, Person
# and Company into document indexable by ElasticSearch.
# Links between Persons, Person and Company, Companies, Person and Country,
# Company and Country is also converted to subdocuments and attached to
# Person/Company documents. Because Person and Company needs different
# subdocuments, Person2Company has two different methods, to_person_dict and
# to_company_dict. For the same reason Person2Person and Company2Company has
# to_dict/to_dict_reverse because same link provides info to both persons.


class Company(models.Model, AbstractNode):
    HEADS_CLASSIFIERS = (
        re.compile(r"^керівник$"),
        re.compile(r"^в\.о\. керівника$"),
        re.compile(r"^директор$"),
        re.compile(r"^в.о директора$"),
        re.compile(r"^генеральний директор$"),
        re.compile(r"^в\.о\. генерального директора$"),
        re.compile(r"^начальник$"),
        re.compile(r"^в\.о\. начальника$"),
        re.compile(r"^ліквідатор$"),
        re.compile(r"^прокурор області$"),
        re.compile(r"^військовий прокурор$"),
        re.compile(r"^генеральний прокурор$"),
        re.compile(r"^надзвичайний і повноважний посол$"),
        re.compile(r"^прем’єр-міністр$"),
        re.compile(r"^президент$"),
        re.compile(r"^підписант$"),
        re.compile(r"^номінальний директор$"),
        re.compile(r"^министр"),
        re.compile(r"^в\.о\. министра"),
        re.compile(r"^голова"),
        re.compile(r"^в\.о\. голови"),
        re.compile(r"^керуючий"),
        re.compile(r"^голова$"),
        re.compile(r"^керуючий$"),
    )

    _status_choices = {
        0: _("інформація відсутня"),
        1: _("зареєстровано"),
        2: _("припинено"),
        3: _("в стані припинення"),
        4: _("зареєстровано, свідоцтво про державну реєстрацію недійсне"),
        5: _("порушено справу про банкрутство"),
        6: _("порушено справу про банкрутство (санація)"),
        7: _("розпорядження майном"),
        8: _("ліквідація"),
    }

    name = models.CharField("Повна назва", max_length=512)
    short_name = models.CharField("Скорочена назва", max_length=200, blank=True)

    also_known_as = models.TextField("Назви іншими мовами або варіації", blank=True)

    publish = models.BooleanField("Опублікувати", default=True)
    founded = models.DateField("Дата створення", blank=True, null=True)
    founded_details = models.IntegerField(
        "Дата створення: точність",
        choices=((0, "Точна дата"), (1, "Рік та місяць"), (2, "Тільки рік")),
        default=0,
    )

    status = models.IntegerField(
        "Поточний стан", choices=_status_choices.items(), default=0
    )
    closed_on = models.DateField("Дата припинення", blank=True, null=True)
    closed_on_details = models.IntegerField(
        "Дата припинення: точність",
        choices=((0, "Точна дата"), (1, "Рік та місяць"), (2, "Тільки рік")),
        default=0,
    )

    @property
    def founded_human(self):
        return render_date(self.founded, self.founded_details)

    state_company = models.BooleanField("Керівник — ПЕП", default=False)

    legal_entity = models.BooleanField("Юрособа", default=True)

    edrpou = models.CharField("ЄДРПОУ", max_length=50, blank=True)

    zip_code = models.CharField("Індекс", max_length=20, blank=True)
    city = models.CharField("Місто", max_length=255, blank=True)
    street = models.CharField("Вулиця", max_length=100, blank=True)
    appt = models.CharField("№ будинку, офісу", max_length=50, blank=True)
    raw_address = models.TextField('"Сира" адреса', blank=True)

    wiki = RedactorField("Вікі-стаття", blank=True)

    other_founders = RedactorField(
        "Інші засновники", help_text="Через кому, не PEP", blank=True
    )

    other_recipient = models.CharField(
        "Бенефіціарій", help_text="Якщо не є PEPом", blank=True, max_length=200
    )

    other_owners = RedactorField(
        "Інші власники", help_text="Через кому, не PEP", blank=True
    )

    other_managers = RedactorField(
        "Інші керуючі", help_text="Через кому, не PEP", blank=True
    )

    bank_name = RedactorField("Фінансова інформація", blank=True)

    sanctions = RedactorField("Санкції", blank=True)

    related_companies = models.ManyToManyField(
        "self", through="Company2Company", symmetrical=False
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

    public_office = models.BooleanField("Держ.орган", default=False)
    political_party = models.BooleanField("Партія", default=False)
    state_enterprise = models.BooleanField("Держ. власність", default=False)
    affiliated_with_pep = models.BooleanField("Пов'язана з ПЕП", default=False)
    bank = models.BooleanField("Банк", default=False)
    service_provider = models.BooleanField("Надавач послуг", default=False)
    _last_modified = models.DateTimeField("Остання зміна", null=True, blank=True)
    proofs = GenericRelation(
        "RelationshipProof", verbose_name="Посилання, соціальні мережі та документи"
    )

    @staticmethod
    def autocomplete_search_fields():
        return ("id__iexact", "short_name__icontains", "name__icontains", "also_known_as__icontains")

    def __unicode__(self):
        return self.short_name or self.name

    def to_dict(self):
        d = model_to_dict(
            self,
            fields=[
                "id",
                "name_uk",
                "short_name_uk",
                "name_en",
                "short_name_en",
                "state_company",
                "edrpou",
                "wiki",
                "city",
                "street",
                "other_founders",
                "other_recipient",
                "other_owners",
                "other_managers",
                "bank_name",
                "also_known_as",
            ],
        )

        d["related_persons"] = [
            i.to_person_dict()
            for i in self.from_persons.prefetch_related("from_person")
        ]

        d["related_countries"] = [
            i.to_dict() for i in self.from_countries.prefetch_related("to_country")
        ]

        d["related_companies"] = [
            i.to_dict() for i in self.to_companies.prefetch_related("to_company")
        ] + [
            i.to_dict_reverse()
            for i in self.from_companies.prefetch_related("from_company")
        ]

        d["status"] = self.get_status_display()
        d["status_en"] = translate_into(self.get_status_display())
        d["founded"] = self.founded_human
        d["closed"] = self.closed_on_human
        d["last_modified"] = self.last_modified

        suggestions = []

        for field in (
            d["name_uk"],
            d["short_name_uk"],
            d["name_en"],
            d["short_name_en"],
        ):
            if not field:
                continue

            chunks = list(map(lambda x: x.strip("'\",.-“”«»"), field.split(" ")))

            for i in xrange(len(chunks)):
                variant = copy(chunks)
                variant = [variant[i]] + variant[:i] + variant[i + 1 :]
                suggestions.append(" ".join(variant))

        if self.edrpou:
            edrpou_chunks = list(
                filter(
                    None,
                    map(
                        unicode.strip,
                        re.split("([a-z]+)", self.edrpou, flags=re.IGNORECASE),
                    ),
                )
            )

            suggestions += edrpou_chunks
            suggestions.append(self.edrpou.lstrip("0"))

            if self.edrpou.isdigit():
                suggestions.append(self.edrpou.rjust(8, "0"))

            d["code_chunks"] = edrpou_chunks

        d["name_suggest"] = [{"input": x} for x in set(suggestions)]

        d["name_suggest_output"] = d["short_name_uk"] or d["name_uk"]
        d["name_suggest_output_en"] = d["short_name_en"] or d["name_en"]

        d["_id"] = d["id"]

        return d

    def save(self, *args, **kwargs):
        if not self.name_en:
            t = Ua2EnDictionary.objects.filter(
                term__iexact=lookup_term(self.name_uk)
            ).first()

            if t and t.translation:
                self.name_en = t.translation

        if not self.short_name_en:
            t = Ua2EnDictionary.objects.filter(
                term__iexact=lookup_term(self.short_name_uk)
            ).first()

            if t and t.translation:
                self.short_name_en = t.translation

        edrpou = self.edrpou or ""
        if " " in edrpou and edrpou.strip() and ":" not in edrpou:
            self.edrpou = self.edrpou.replace(" ", "")

        super(Company, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("company_details", kwargs={"company_id": self.pk})

    def localized_url(self, locale):
        curr_lang = get_language()
        activate(locale)
        url = self.get_absolute_url()
        activate(curr_lang)
        return url

    @property
    def url_uk(self):
        return settings.SITE_URL + self.localized_url("uk")

    @property
    def all_related_persons(self):
        related_persons = [
            (i.relationship_type_uk, deepcopy(i.from_person), i)
            for i in self.from_persons.prefetch_related("from_person")
            .defer(
                "from_person__reputation_assets",
                "from_person__reputation_crimes",
                "from_person__reputation_manhunt",
                "from_person__reputation_convictions",
                "from_person__wiki",
                "from_person__names",
                "from_person__hash",
            )
            .order_by("from_person__last_name_uk", "from_person__first_name_uk")
        ]

        res = {
            "managers": [],
            "founders": [],
            "sanctions": [],
            "bank_customers": [],
            "rest": [],
            "all": [],
        }

        for rtp, p, rel in related_persons:
            add_to_rest = True
            p.rtype = rtp
            p.connection = rel

            res["all"].append(p)

            if any(map(lambda x: x.search(rtp.lower()), self.HEADS_CLASSIFIERS)):
                if (
                    rel.date_finished
                    and ceil_date(rel.date_finished, rel.date_finished_details)
                    <= date.today()
                ):
                    add_to_rest = True
                else:
                    res["managers"].append(p)
                    add_to_rest = False

            elif rtp.lower() in [
                "засновник",
                "учасник",
                "власник",
                "бенефіціарний власник",
                "номінальний власник",
                "колишній засновник/учасник",
            ]:
                res["founders"].append(p)
                add_to_rest = False

            elif rtp.lower() in ["клієнт банку"]:
                res["bank_customers"].append(p)
                add_to_rest = False

            if p.reputation_sanctions:
                res["sanctions"].append(p)
                add_to_rest = False

            if add_to_rest:
                res["rest"].append(p)

        return res

    @property
    def all_related_countries(self):
        related_countries = [
            (i.relationship_type, deepcopy(i.to_country), i)
            for i in self.from_countries.prefetch_related("to_country")
        ]

        res = defaultdict(list)

        for rtp, p, rel in related_countries:
            p.rtype = rtp
            p.connection = rel

            if rtp == "registered_in":
                res[rtp].append(p)
            else:
                res["rest"].append(p)

        return res

    # TODO: Request in bulk in all_related_companies?
    @property
    def foreign_registration(self):
        return self.from_countries.prefetch_related("to_country").filter(
            relationship_type="registered_in"
        )

    @property
    def all_related_companies(self):
        related_companies = [
            (i.relationship_type, deepcopy(i.to_company), i, True)
            for i in self.to_companies.prefetch_related("to_company").defer(
                "to_company__wiki",
                "to_company__other_founders",
                "to_company__other_recipient",
                "to_company__other_owners",
                "to_company__other_managers",
                "to_company__bank_name",
                "to_company__sanctions",
            )
        ] + [
            (i.reverse_relationship_type, deepcopy(i.from_company), i, False)
            for i in self.from_companies.prefetch_related("from_company").defer(
                "from_company__wiki",
                "from_company__other_founders",
                "from_company__other_recipient",
                "from_company__other_owners",
                "from_company__other_managers",
                "from_company__bank_name",
                "from_company__sanctions",
            )
        ]

        res = {"founders": [], "rest": [], "banks": [], "all": []}

        for rtp, p, rel, direction in sorted(related_companies, key=lambda x: x[1].name_uk):
            p.rtype = rtp
            p.connection = rel
            p.direction = direction

            if rtp in [
                "Засновник",
                "Співзасновник",
                "Колишній власник/засновник",
                "Колишній співвласник/співзасновник",
            ]:
                res["founders"].append(p)
            elif rtp == "Клієнт банку":
                res["banks"].append(p)
            else:
                res["rest"].append(p)

            res["all"].append(p)

        return res

    def get_node(self):
        res = super(Company, self).get_node()

        node = {
            "description": self.edrpou,
            "state_company": self.state_company,
            "is_closed": bool(self.closed_on_human),
        }

        curr_lang = get_language()
        for lang in settings.LANGUAGE_CODES:
            activate(lang)
            node.update({
                "name": self.short_name or self.name,
                "full_name": self.name,
                "kind": unicode(
                    ugettext_lazy("Державна компанія чи установа")
                    if self.state_company
                    else ugettext_lazy("Приватна компанія")
                )
            })

        activate(curr_lang)

        res["data"].update(node)

        return res

    # temporary hack to keep old viz afloat
    def get_node_old(self):
        res = super(Company, self).get_node()

        node = {
            "name": self.short_name or self.name,
            "full_name": self.name,
            "description": self.edrpou,
            "state_company": self.state_company,
            "is_closed": bool(self.closed_on_human),
            "kind": unicode(
                ugettext_lazy("Державна компанія чи установа")
                if self.state_company
                else ugettext_lazy("Приватна компанія")
            ),
        }

        res["data"].update(node)

        return res

    def get_node_info(self, with_connections=False):
        this_node = self.get_node_old()
        nodes = [this_node]
        edges = []
        all_connected = set()

        # Because of a complicated logic here we are piggybacking on
        # existing method that handles both directions of relations
        for p in self.all_related_persons["rest"]:
            if p.rtype.lower() in [_("клієнт банку")]:
                continue                    

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
                            "target": this_node["data"]["id"],
                            "source": child_node_id,
                            "is_latest": True,
                        }
                    }
                )

            all_connected.add(child_node_id)

        for c in self.all_related_companies["all"]:
            child_node_id = c.get_node_id()

            if with_connections:
                child_node = c.get_node_info(False)
                nodes += child_node["nodes"]
                edges += child_node["edges"]
                if c.direction:
                    source = child_node_id
                    target = this_node["data"]["id"]
                else:
                    source = this_node["data"]["id"]
                    target = child_node_id

                edges.append(
                    {
                        "data": {
                            "relation": unicode(c.connection.relationship_type),
                            "model": c.connection._meta.model_name,
                            "pk": c.connection.pk,
                            "id": "{}-{}".format(
                                c.connection._meta.model_name, c.connection.pk
                            ),
                            "source": source,
                            "share": float(c.connection.equity_part or 0),
                            "target": target,
                            "is_latest": True,
                        }
                    }
                )

            all_connected.add(child_node_id)

        this_node["data"]["all_connected"] = list(all_connected)
        return {"edges": edges, "nodes": nodes}


    @property
    def closed_on_human(self):
        return render_date(self.closed_on, self.closed_on_details)

    @property
    def last_modified(self):
        c2c_conn = Company2Company.objects.filter(
            Q(from_company=self) | Q(to_company=self)
        ).aggregate(mm=Max("_last_modified"))["mm"]

        c2p_conn = Person2Company.objects.filter(to_company=self).aggregate(
            mm=Max("_last_modified")
        )["mm"]

        c2cont_conn = Company2Country.objects.filter(from_company=self).aggregate(
            mm=Max("_last_modified")
        )["mm"]

        seq = list(
            filter(
                None,
                [
                    c2c_conn,
                    c2p_conn,
                    c2cont_conn,
                    self.last_change,
                    self._last_modified,
                ],
            )
        )
        if seq:
            return max(seq)

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
            for proof in c.connection.proofs.all():
                if not proof.proof_document:
                    continue
                proofs.append(proof)

        seen = set()
        for proof in proofs + list(self.proofs.all()):
            if proof.proof_document_id not in seen:
                proofs_by_cat[proof.proof_document.doc_type].append(proof)

                seen.add(proof.proof_document_id)

        proofs_by_cat["misc"] += proofs_by_cat["other"]
        del proofs_by_cat["other"]

        return OrderedDict(
            (Document.DOC_TYPE_CHOICES[k], proofs_by_cat[k])
            for k in Document.DOC_TYPE_CHOICES.keys()
        )

    objects = CompanyManager()

    class Meta:
        verbose_name = "Юридична особа"
        verbose_name_plural = "Юридичні особи"

        permissions = (("export_companies", "Can export the dataset of companies"),)


class CompanyCategories(Company):
    class Meta:
        proxy = True
        verbose_name = "Категорізація юр. осіб"
        verbose_name_plural = "Категорізація юр. осіб"
