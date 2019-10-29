# coding: utf-8
from __future__ import unicode_literals
import re
import logging
from collections import defaultdict

from django.db import models
from django.conf import settings
from django.forms.models import model_to_dict
from django.utils.translation import ugettext_noop as _
from django.utils.translation import ugettext_lazy, get_language

from jsonfield import JSONField
from cacheops import cached

from core.fields import RedactorField
from core.utils import (
    parse_fullname, parse_family_member, RELATIONS_MAPPING, render_date,
    get_exchange_rate)

from core.model.connections import Person2Person
from core.model.exc import CannotResolveRelativeException

logger = logging.getLogger(__name__)


class Declaration(models.Model):
    STATUS_CHOICES = (
        ('p', 'Не перевірено'),
        ('r', 'Не підходить'),
        ('a', 'Опубліковано'),
        ('c', 'Перевірити'),
    )

    declaration_id = models.CharField(
        "Ідентифікатор", max_length=50, db_index=True)

    last_name = models.CharField("Прізвище", max_length=40, blank=True)
    first_name = models.CharField("Ім'я", max_length=40, blank=True)
    patronymic = models.CharField("По-батькові", max_length=40, blank=True)
    position = models.CharField("Посада", max_length=512, blank=True)
    office = models.CharField("Відомство", max_length=512, blank=True)
    region = models.CharField("Регіон", max_length=50, blank=True)
    doc_type = models.CharField("Тип декларації", max_length=50, blank=True)
    year = models.CharField("Рік", max_length=4, blank=True, db_index=True)
    source = JSONField(blank=True)
    url = models.URLField("Посилання", max_length=512, blank=True)
    confirmed = models.CharField(
        "Підтверджено", max_length=1, choices=STATUS_CHOICES, default="p",
        db_index=True)
    fuzziness = models.IntegerField("Відстань", default=0)
    person = models.ForeignKey("Person", default=None, related_name="declarations")
    nacp_declaration = models.BooleanField(
        "Декларація НАЗК", default=False, db_index=True)

    relatives_populated = models.BooleanField(
        "Родини немає, або вже внесена до БД", default=False, db_index=True)

    to_link = models.BooleanField(
        "Декларація для профілів", default=False, db_index=True)

    to_watch = models.BooleanField(
        "Декларація для моніторінгу звільнень", default=False, db_index=True)

    acknowledged = models.BooleanField(
        "Відмоніторено", default=False, db_index=True)

    submitted = models.DateField(
        "Подана", blank=True, null=True, db_index=True)

    batch_number = models.IntegerField("Номер теки", default=0, db_index=True)

    def get_url(self):
        url = self.url
        if get_language() == "en" and self.nacp_declaration:
            return settings.DECLARATION_DETAILS_EN_ENDPOINT.format(self.declaration_id)

        return url

    def to_dict(self):
        d = model_to_dict(self, fields=[
            "year", "position_uk", "office_uk", "region_uk",
            "position_en", "office_en", "region_en", "url"
        ])

        income = self.get_income()

        try:
            d["income"] = float(income["income_of_declarant"])
        except (ValueError, TypeError):
            pass

        try:
            d["family_income"] = float(income["income_of_family"])
        except (ValueError, TypeError):
            pass

        return d

    @property
    def family(self):
        if not self.source:
            return []

        res = []
        if ("family" in self.source["general"] and
                self.source["general"]["family"]):

            res = [
                {
                    "relation":
                        member.get(
                            "relations",
                            member.get("relations_other", "")),

                    "name": member.get("family_name", "")
                } for member in self.source["general"]["family"]
                if (
                    member.get("family_name", "") and
                    (member["relations"] + member.get("relations_other", ""))
                )
            ]
        elif ("family_raw" in self.source["general"] and
                self.source["general"]["family_raw"]):
            res = map(
                parse_family_member,
                filter(None, self.source["general"]["family_raw"].split(";")))

        res = filter(None, res)

        for i, r in enumerate(res):
            res[i]["mapped"] = RELATIONS_MAPPING.get(
                r["relation"].lower(), "особи, які спільно проживають")

            (res[i]["last_name"], res[i]["first_name"], res[i]["patronymic"],
                res[i]["dob"]) = parse_fullname(r["name"])

        return res

    def __unicode__(self):
        return "%s %s" % (self.person, self.declaration_id)

    @cached(timeout=60 * 60)
    def get_income(self):
        resp = {
            "year": self.year,
            "position": self.position,
            "office": self.office,
            "url": self.get_url(),
            "income_of_declarant": ugettext_lazy("Не зазначено"),
            "income_of_family": ugettext_lazy("Не зазначено"),
            "expenses_of_declarant": ugettext_lazy("Не зазначено"),
        }

        if self.nacp_declaration:
            resp["income_of_declarant"] = 0
            resp["income_of_family"] = 0
            resp["expenses_of_declarant"] = 0
            if isinstance(self.source["nacp_orig"].get("step_11"), dict):
                for income in self.source["nacp_orig"]["step_11"].values():
                    try:
                        person = income.get("person", "1")
                        income_size = float(income.get("sizeIncome", "0"))

                        if person == "1":
                            resp["income_of_declarant"] += income_size
                        else:
                            resp["income_of_family"] += income_size
                    except (ValueError, AttributeError):
                        pass

            if isinstance(self.source["nacp_orig"].get("step_14"), dict):
                for expense in self.source["nacp_orig"]["step_14"].values():
                    try:
                        expense_amount = float(expense.get("costAmount", "0"))
                        resp["expenses_of_declarant"] += expense_amount
                    except (ValueError, AttributeError):
                        pass
        else:
            resp["expenses_of_declarant"] = ugettext_lazy("Не зазначалось")

            if "income" in self.source:
                resp["income_of_declarant"] = self.source["income"]['5'].get(
                    "value", ugettext_lazy("Не зазначено"))
                resp["income_of_family"] = self.source["income"]['5'].get(
                    "family", ugettext_lazy("Не зазначено"))

        return resp


    # @cached(timeout=60 * 60)
    def get_assets(self):
        resp = {
            "year": self.year,
            "url": self.get_url(),
            "nacp_declaration": self.nacp_declaration,
            "total_uah": {
                "declarant": 0.,
                "family": 0.,
            },
            "cash": {
                "declarant": {
                    "USD": 0.,
                    "UAH": 0.,
                    "EUR": 0.,
                    "OTH": [],
                },
                "family": {
                    "USD": 0.,
                    "UAH": 0.,
                    "EUR": 0.,
                    "OTH": [],
                }
            },
            "accounts": {
                "declarant": {
                    "USD": 0.,
                    "UAH": 0.,
                    "EUR": 0.,
                    "OTH": [],
                    "banks": set(),
                },
                "family": {
                    "USD": 0.,
                    "UAH": 0.,
                    "EUR": 0.,
                    "OTH": [],
                    "banks": set(),
                }
            },
            "misc": {
                "declarant": {
                    "USD": 0.,
                    "UAH": 0.,
                    "EUR": 0.,
                    "OTH": [],
                },
                "family": {
                    "USD": 0.,
                    "UAH": 0.,
                    "EUR": 0.,
                    "OTH": [],
                }
            }
        }

        if self.nacp_declaration:
            data = self.source["nacp_orig"]

            if isinstance(data.get("step_12"), dict):
                for cash_rec in data["step_12"].values():
                    if isinstance(cash_rec, dict):
                        k = "misc"
                        rec_type = cash_rec.get("objectType", "").lower()
                        owner = "declarant" if cash_rec.get("person", "1") == "1" else "family"
                        amount = float(cash_rec.get("sizeAssets", "0") or "0")

                        currency = cash_rec.get("assetsCurrency", "UAH").upper()

                        if rec_type == "кошти, розміщені на банківських рахунках":
                            bank_name = cash_rec.get("organization_ua_company_name") or \
                                cash_rec.get("organization_ukr_company_name", "")

                            bank_name = bank_name.strip()
                            k = "accounts"
                            resp[k][owner]["banks"].add(bank_name)
                        elif rec_type == "готівкові кошти":
                            k = "cash"

                        if currency in ("UAH", "USD", "EUR"):
                            resp[k][owner][currency] += amount
                        else:
                            resp[k][owner]["OTH"].append(
                                {"amount": amount, "currency": currency}
                            )

                        resp["total_uah"][owner] += amount * get_exchange_rate(currency, self.year)

        else:
            for d_key, owner in (("45", "declarant"), ("51", "family")):
                for a in self.source.get("banks", {}).get(d_key, []):
                    try:
                        currency = a.get("sum_units", "UAH") or "UAH"
                        amount = float(a.get("sum", 0.))
                        if currency == "грн":
                            currency = "UAH"

                        resp["total_uah"][owner] += amount * get_exchange_rate(currency, self.year)

                        if currency in ("UAH", "USD", "EUR"):
                            resp["accounts"][owner][currency] += amount
                        else:
                            resp["accounts"][owner]["OTH"].append(
                                {"amount": amount, "currency": currency}
                            )
                    except ValueError:
                        continue

        return resp

    def get_gifts(self):
        resp = {
            "year": self.year,
            "url": self.get_url(),
            "gifts_of_declarant": ugettext_lazy("Не зазначено"),
            "gifts_of_family": ugettext_lazy("Не зазначено"),
        }

        if self.nacp_declaration:
            resp["gifts_of_declarant"] = 0
            resp["gifts_of_family"] = 0
            if isinstance(self.source["nacp_orig"].get("step_11"), dict):
                for income in self.source["nacp_orig"]["step_11"].values():
                    try:
                        rec_type = income.get("objectType", "").lower()
                        if rec_type not in [
                                "подарунок у негрошовій формі",
                                "подарунок у грошовій формі",
                                "благодійна допомога", "приз"]:
                            continue

                        person = income.get("person", "1")
                        income_size = float(income.get("sizeIncome", "0"))

                        if person == "1":
                            resp["gifts_of_declarant"] += income_size
                        else:
                            resp["gifts_of_family"] += income_size
                    except (ValueError, AttributeError):
                        pass
        else:
            if "income" in self.source:
                resp["gifts_of_declarant"] = self.source["income"]['11'].get(
                    "value", ugettext_lazy("Не зазначено"))

                resp["gifts_of_family"] = self.source["income"]['11'].get(
                    "family", ugettext_lazy("Не зазначено"))

        return resp

    def get_liabilities(self):
        resp = {
            "year": self.year,
            "url": self.get_url(),
            "liabilities_of_declarant": defaultdict(float),
            "liabilities_of_family": defaultdict(float),
        }

        if self.nacp_declaration:
            if isinstance(self.source["nacp_orig"].get("step_13"), dict):
                for liability in self.source["nacp_orig"]["step_13"].values():
                    try:
                        person = liability.get("person", "1")
                        liability_amount = float(liability.get("sizeObligation", "0") or 0)
                        currency = liability.get("currency", "UAH") or "UAH"

                        if person == "1":
                            resp["liabilities_of_declarant"][currency] += liability_amount
                        else:
                            resp["liabilities_of_family"][currency] += liability_amount
                    except (ValueError, AttributeError):
                        pass
        else:
            if "liabilities" in self.source:
                for field in ["54", "55", "56", "57", "58", "59"]:
                    if field in self.source["liabilities"]:
                        try:
                            resp["liabilities_of_declarant"]["UAH"] += float(
                                (self.source["liabilities"][field].get("sum", "0") or "0").replace(",", "."))
                        except (ValueError, UnicodeEncodeError):
                            pass

                for field in ["60", "61", "62", "63", "64"]:
                    if field in self.source["liabilities"]:
                        try:
                            resp["liabilities_of_family"]["UAH"] += float(
                                (self.source["liabilities"][field].get("sum", "0") or "0").replace(",", "."))
                        except (ValueError, UnicodeEncodeError):
                            pass

        return resp

    def get_active_assets(self):
        resp = {
            "year": self.year,
            "url": self.get_url(),
            "assets_of_declarant": defaultdict(list),
            "assets_of_family": defaultdict(list),
        }

        realty = self.get_real_estate()
        vehicles = self.get_vehicles()

        resp["assets_of_declarant"].update(realty["assets_of_declarant"])
        resp["assets_of_family"].update(realty["assets_of_family"])
        resp["assets_of_declarant"].update(vehicles["assets_of_declarant"])
        resp["assets_of_family"].update(vehicles["assets_of_family"])

        return resp

    def get_real_estate(self):
        def _convert_space_values(total_area, area_units):
            areas_koef = {
                "га": 10000,
                "cоток": 100
            }

            try:
                total_area = str(total_area).replace(',', '.')

                if not total_area:
                    return 0

                if not area_units:
                    return float(total_area)

                return float(total_area) * areas_koef.get(area_units, 1)
            except ValueError:
                return 0

        def _get_key_for_paper(f, field):
            return "{}.{}.{}".format(f.get("space"), field, f.get("region")).lower()

        def _get_key_for_nacp(f, total_area):
            return "{}.{}.{}".format(f.get("ua_cityType"), total_area, f.get("objectType")).lower()

        resp = {
            "year": self.year,
            "url": self.get_url(),
            "assets_of_declarant": defaultdict(list),
            "assets_of_family": defaultdict(list),
        }

        seen = set()

        if self.nacp_declaration:
            ESTATE_OBJECT_TYPE_MAPPING = {
                'квартира': 'apartments',
                'земельна ділянка': 'land',
                'житловий будинок': 'houses',
                'кімната': 'other',
                'гараж': 'other',
                'садовий (дачний) будинок': 'other',
                'офіс': 'other',
                'інше': 'other'
            }
            if isinstance(self.source["nacp_orig"].get("step_3"), dict):
                for src in ["declarant", "family"]:
                    for asset in self.source["nacp_orig"]["step_3"].values():
                        try:
                            person = asset.get("person", "1")
                            if src == "declarant" and person != "1":
                                continue

                            if src == "family" and person == "1":
                                continue

                            area = _convert_space_values(asset.get("totalArea", "0"), "")
                            k = _get_key_for_nacp(asset, area)
                            rec_type = asset.get("objectType", "").lower()
                            section = ESTATE_OBJECT_TYPE_MAPPING[rec_type]

                            if person == "1":
                                seen.add(k)
                                resp["assets_of_declarant"][section].append(area)
                            else:
                                if k in seen:
                                    continue

                                seen.add(k)
                                resp["assets_of_family"][section].append(area)
                        except (ValueError, AttributeError):
                            pass
        else:
            if "estate" in self.source:
                ESTATE_OBJECT_TYPE_MAPPING_DECLARANT = {
                    "23": "land",
                    "24": "houses",
                    "25": "apartments",
                    "26": "other",
                    "27": "other",
                    "28": "other",
                }

                ESTATE_OBJECT_TYPE_MAPPING_FAMILY = {
                    "29": "land",
                    "30": "houses",
                    "31": "apartments",
                    "32": "other",
                    "33": "other",
                    "34": "other",
                }

                for field in ESTATE_OBJECT_TYPE_MAPPING_DECLARANT.keys():
                    if field in self.source["estate"]:
                        section = ESTATE_OBJECT_TYPE_MAPPING_DECLARANT[field]

                        try:
                            for f in self.source["estate"][field]:
                                seen.add(_get_key_for_paper(f, section))
                                resp["assets_of_declarant"][section].append(
                                    _convert_space_values(f.get("space", "0"), f.get("space_units"))
                                )
                        except (ValueError, UnicodeEncodeError):
                            pass

                for field in ESTATE_OBJECT_TYPE_MAPPING_FAMILY.keys():
                    if field in self.source["estate"]:
                        section = ESTATE_OBJECT_TYPE_MAPPING_FAMILY[field]

                        try:
                            for f in self.source["estate"][field]:
                                k = _get_key_for_paper(f, section)

                                if k in seen:
                                    continue

                                seen.add(k)

                                resp["assets_of_family"][section].append(
                                    _convert_space_values(f.get("space", "0"), f.get("space_units"))
                                )
                        except (ValueError, UnicodeEncodeError):
                            pass

        return resp

    def get_vehicles(self):
        def _normalize_key(src):
            s = re.sub(
                "[.,\/#!$%\^&\*;:{}=\-_`~()]",
                "",
                src
            )

            return re.sub("\s+", "", s).lower()

        def _get_key_for_paper(f):
            return _normalize_key(
                "{}|{}|{}".format(
                    f.get("brand", ""),
                    f.get("model", ""),
                    f.get("graduationYear", "")
                )
            )

        def _get_key_for_nacp(f):
            return _normalize_key(
                "{}|{}|{}".format(
                    f.get("brand", ""),
                    f.get("brand_info", ""),
                    f.get("year", "")
                )
            )

        resp = {
            "year": self.year,
            "url": self.get_url(),
            "assets_of_declarant": defaultdict(list),
            "assets_of_family": defaultdict(list),
        }

        seen = set()

        if self.nacp_declaration:
            if isinstance(self.source["nacp_orig"].get("step_6"), dict):
                for src in ["declarant", "family"]:
                    for asset in self.source["nacp_orig"]["step_6"].values():
                        try:
                            person = asset.get("person", "1")
                            if src == "declarant" and person != "1":
                                continue

                            if src == "family" and person == "1":
                                continue

                            k = _get_key_for_nacp(asset)
                            vehicle = "{} {} {}".format(
                                asset.get("brand", ""),
                                asset.get("model", ""),
                                asset.get("graduationYear", "")
                            )

                            if person == "1":
                                seen.add(k)
                                resp["assets_of_declarant"]["vehicles"].append(vehicle)
                            else:
                                if k in seen:
                                    continue

                                seen.add(k)
                                resp["assets_of_family"]["vehicles"].append(vehicle)
                        except (ValueError, AttributeError):
                            pass
        else:
            if "vehicle" in self.source:
                for field in ["34", "35", "36", "37", "38", "39"]:
                    if field in self.source["vehicle"]:
                        try:
                            for f in self.source["vehicle"][field]:
                                seen.add(_get_key_for_paper(f))

                                resp["assets_of_declarant"]["vehicles"].append(
                                    "{} {} {}".format(f.get("brand", ""), f.get("brand_info", ""), f.get("year", ""))
                                )
                        except (ValueError, UnicodeEncodeError):
                            pass

                for field in ["40", "41", "42", "43", "44"]:
                    if field in self.source["vehicle"]:
                        try:
                            for f in self.source["vehicle"][field]:
                                k = _get_key_for_paper(f)

                                if k in seen:
                                    continue

                                seen.add(k)
                                resp["assets_of_family"]["vehicles"].append(
                                    "{} {} {}".format(f.get("brand", ""), f.get("brand_info", ""), f.get("year", ""))
                                )
                        except (ValueError, UnicodeEncodeError):
                            pass
        return resp

    @property
    def declaration_type(self):
        if self.nacp_declaration:
            return self.source["intro"].get("doc_type", "Щорічна")
        else:
            return "Щорічна"

    def resolve_person(self, family_id):
        """
        Finds the relative mentioned in the declaration in
        PEP db.
        Returns person id and a flag set to true, if it was fuzzy
        match
        """

        if str(family_id) == "1":
            return self.person, False

        def _is_fuzzy_match(declaration_rec, person_rec):
            if (declaration_rec["lastname"].strip().lower() !=
                    person_rec.last_name.strip().lower()):
                return True
            if (declaration_rec["firstname"].strip().lower() !=
                    person_rec.first_name.strip().lower()):
                return True
            if (declaration_rec["middlename"].strip().lower() !=
                    person_rec.patronymic.strip().lower()):
                return True

            return False

        data = self.source["nacp_orig"]
        family = data.get("step_2")

        if isinstance(family, dict):
            if not family_id or family_id not in family:
                raise CannotResolveRelativeException(
                    "Cannot find person %s in the declaration %s" % (
                        family_id, self.declaration_id)
                )

            member = family[family_id]
        else:
            raise CannotResolveRelativeException(
                "Cannot find family section in the declaration %s" % (
                    self.declaration_id)
            )

        chunk1 = list(Person2Person.objects.filter(
            from_person_id=self.person_id,
            to_person__last_name_uk__iexact=member["lastname"].strip(),
            to_person__first_name_uk__iexact=member["firstname"].strip(),
            to_person__patronymic_uk__iexact=member["middlename"].strip()
        ).select_related("to_person")) + list(Person2Person.objects.filter(
            from_person_id=self.person_id,
            to_person__last_name_uk__trigram_similar=member["lastname"].strip(),
            to_person__first_name_uk__trigram_similar=member["firstname"].strip(),
            to_person__patronymic_uk__trigram_similar=member["middlename"].strip()
        ).select_related("to_person"))

        chunk2 = list(Person2Person.objects.filter(
            to_person_id=self.person_id,
            from_person__last_name_uk__iexact=member["lastname"].strip(),
            from_person__first_name_uk__iexact=member["firstname"].strip(),
            from_person__patronymic_uk__iexact=member["middlename"].strip()
        ).select_related("from_person")) + list(Person2Person.objects.filter(
            to_person_id=self.person_id,
            from_person__last_name_uk__trigram_similar=member["lastname"].strip(),
            from_person__first_name_uk__trigram_similar=member["firstname"].strip(),
            from_person__patronymic_uk__trigram_similar=member["middlename"].strip()
        ).select_related("from_person"))

        if len(set(chunk1)) + len(set(chunk2)) > 1:
            raise CannotResolveRelativeException(
                "Uh, oh, more than one connection between %s and %s %s %s" %
                (self.person, member["lastname"], member["firstname"],
                 member["middlename"])
            )

        for conn in chunk1:
            fuzzy_match = _is_fuzzy_match(member, conn.to_person)
            if fuzzy_match:
                logger.warning(
                    "It was fuzzy match between %s %s %s and the declarant %s" % (
                        member["lastname"], member["firstname"],
                        member["middlename"], conn.to_person)
                )
            return conn.to_person, fuzzy_match

        for conn in chunk2:
            fuzzy_match = _is_fuzzy_match(member, conn.from_person)
            if fuzzy_match:
                logger.warning(
                    "It was fuzzy match between %s %s %s and the declarant %s" % (
                        member["lastname"], member["firstname"],
                        member["middlename"], conn.from_person)
                )

            return conn.from_person, fuzzy_match

        raise CannotResolveRelativeException(
            "Cannot find person %s %s %s for the declarant %s" % (
                member["lastname"], member["firstname"], member["middlename"],
                self.person
            )
        )

    class Meta:
        verbose_name = "Декларація"
        verbose_name_plural = "Декларації"
        indexes = [
            models.Index(fields=['confirmed', 'fuzziness', 'batch_number']),
        ]

        unique_together = [
            ["person", "declaration_id"],
        ]


class DeclarationToLinkManager(models.Manager):
    def get_queryset(self):
        return super(DeclarationToLinkManager, self).get_queryset().filter(to_link=True)


class DeclarationToLink(Declaration):
    class Meta:
        proxy = True
        verbose_name = "Декларація"
        verbose_name_plural = "Декларації"

    objects = DeclarationToLinkManager()


class DeclarationToWatchManager(models.Manager):
    def get_queryset(self):
        return super(DeclarationToWatchManager, self).get_queryset().filter(to_watch=True).order_by(
            "-submitted"
        )


class DeclarationToWatch(Declaration):
    class Meta:
        proxy = True
        verbose_name = "Моніторинг декларацій"
        verbose_name_plural = "Моніторинг декларацій"

    objects = DeclarationToWatchManager()


class DeclarationExtra(models.Model):
    person = models.ForeignKey("Person", related_name="declaration_extras")

    date_confirmed = models.DateField(
        "Дата", blank=True, null=True, db_index=True)

    date_confirmed_details = models.IntegerField(
        "точність",
        choices=(
            (0, "Точна дата"),
            (1, "Рік та місяць"),
            (2, "Тільки рік"),
        ),
        default=0)

    @property
    def date_confirmed_human(self):
        return render_date(self.date_confirmed,
                           self.date_confirmed_details)

    section = models.IntegerField(
        "Розділ декларації",
        choices=(
            (0, _("Загальна сума сукупного доходу, гривні")),
            (1, _("Дарунки, призи, виграші")),
            (2, _("Земельні ділянки")),
            (3, _("Житлові будинки")),
            (4, _("Квартири")),
            (5, _("Інше нерухоме майно")),
            (6, _("Транспортні засоби")),
            (7, _("Вклади у банках")),
            (8, _("Фінансові зобов’язання")),
            (9, _("Інші активи")),
        ),
        default=0,
        db_index=True
    )

    note = RedactorField("Текст")
    address = RedactorField("Адреса", blank=True)
    country = models.ForeignKey("Country", blank=True)

    class Meta:
        verbose_name = "Додаткова інформація про статки"
        verbose_name_plural = "Додаткова інформація про статки"
