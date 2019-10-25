# coding: utf-8
from __future__ import unicode_literals
from collections import OrderedDict


from django.db import models
from django.utils.translation import ugettext_noop as _
from django.contrib.postgres.fields import ArrayField

from core.fields import RedactorField
from core.utils import lookup_term, translate_into
from core.model.base import AbstractRelationship
from core.model.translations import Ua2EnDictionary
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError


class Person2Person(AbstractRelationship):
    _relationships_explained = OrderedDict([
        (_("чоловік"), [_("дружина")]),
        (_("дружина"), [_("чоловік")]),
        (_("чоловік/дружина"), [_("чоловік/дружина")]),
        (_("батько"), [_("син"), _("дочка"), _("син/дочка")]),
        (_("мати"), [_("син"), _("дочка"), _("син/дочка")]),
        (_("батько/мати"), [_("син"), _("дочка"), _("син/дочка")]),
        (_("син"), [_("батько"), _("мати"), _("батько/мати")]),
        (_("дочка"), [_("батько"), _("мати"), _("батько/мати")]),
        (_("син/дочка"), [_("батько"), _("мати"), _("батько/мати")]),
        (_("вітчим"), [_("пасинок"), _("падчерка")]),
        (_("мачуха"), [_("пасинок"), _("падчерка")]),
        (_("пасинок"), [_("вітчим"), _("мачуха")]),
        (_("падчерка"), [_("вітчим"), _("мачуха")]),
        (_("рідний брат"), [_("рідна сестра"), _("рідний брат")]),
        (_("рідна сестра"), [_("рідна сестра"), _("рідний брат")]),
        (_("дід"), [_("внук"), _("внучка")]),
        (_("баба"), [_("внук"), _("внучка")]),
        (_("прадід"), [_("правнук"), _("правнучка")]),
        (_("прабаба"), [_("правнук"), _("правнучка")]),
        (_("внук"), [_("дід"), _("баба")]),
        (_("внучка"), [_("дід"), _("баба")]),
        (_("правнук"), [_("прадід"), _("прабаба")]),
        (_("правнучка"), [_("прадід"), _("прабаба")]),
        (_("зять"), [_("теща"), _("тесть")]),
        (_("невістка"), [_("свекор"), _("свекруха")]),
        (_("тесть"), [_("зять")]),
        (_("теща"), [_("зять")]),
        (_("свекор"), [_("невістка")]),
        (_("свекруха"), [_("невістка")]),
        (_("усиновлювач"), [_("усиновлений")]),
        (_("усиновлений"), [_("усиновлювач")]),
        (_("опікун чи піклувальник"),
         [_("особа, яка перебуває під опікою або піклуванням")]),
        (_("особа, яка перебуває під опікою або піклуванням"),
         [_("опікун чи піклувальник")]),
        (_("особи, які спільно проживають"),
         [_("особи, які спільно проживають")]),
        (_("пов'язані спільним побутом і мають взаємні права та обов'язки"),
         [_("пов'язані спільним побутом і мають взаємні права та обов'язки")]),
        (_("ділові зв'язки"), [_("ділові зв'язки")]),
        (_("особисті зв'язки"), [_("особисті зв'язки")]),
    ])

    from_person = models.ForeignKey(
        "Person", verbose_name="Персона 1", related_name="to_persons")
    to_person = models.ForeignKey(
        "Person", verbose_name="Персона 2", related_name="from_persons")

    from_relationship_type = models.CharField(
        "Персона 1 є",
        choices=(zip(_relationships_explained.keys(),
                     map(_, _relationships_explained.keys()))),
        max_length=100,
        blank=True)

    to_relationship_type = models.CharField(
        "Персона 2 є",
        choices=(zip(_relationships_explained.keys(),
                     map(_, _relationships_explained.keys()))),
        max_length=100,
        blank=True)

    relationship_details = RedactorField(
        "Детальний опис зв'язку", blank=True
    )

    declarations = ArrayField(
        models.IntegerField(),
        verbose_name="Декларації, що підтверджують зв'язок",
        null=True,
        blank=True
    )

    def __unicode__(self):
        return "%s (%s) -> %s (%s)" % (
            self.from_person, self.get_from_relationship_type_display(),
            self.to_person, self.get_to_relationship_type_display())

    def to_dict(self):
        """
        Convert link between two persons into indexable presentation.
        """
        return {
            "date_established": self.date_established_human,
            "date_finished": self.date_finished_human,
            "date_confirmed": self.date_confirmed_human,

            "relationship_type": self.to_relationship_type,
            "relationship_type_en": translate_into(self.to_relationship_type),
            "is_pep": self.to_person.is_pep,
            "person_uk": "%s %s %s" % (
                self.to_person.first_name_uk,
                self.to_person.patronymic_uk,
                self.to_person.last_name_uk),
            "person_en": "%s %s %s" % (
                self.to_person.first_name_en,
                self.to_person.patronymic_en,
                self.to_person.last_name_en),
        }

    def to_dict_reverse(self):
        """
        Convert back link between two persons to indexable presentation.
        """
        return {
            "date_established": self.date_established_human,
            "date_finished": self.date_finished_human,
            "date_confirmed": self.date_confirmed_human,

            "relationship_type": self.from_relationship_type,
            "relationship_type_en": translate_into(self.from_relationship_type),
            "is_pep": self.from_person.is_pep,
            "person_uk": "%s %s %s" % (
                self.from_person.first_name_uk,
                self.from_person.patronymic_uk,
                self.from_person.last_name_uk),
            "person_en": "%s %s %s" % (
                self.from_person.first_name_en,
                self.from_person.patronymic_en,
                self.from_person.last_name_en),
        }

    class Meta:
        verbose_name = "Зв'язок з іншою персоною"
        verbose_name_plural = "Зв'язки з іншими персонами"


class Person2Company(AbstractRelationship):
    _relationships_explained = [
        "Президент",
        "Прем’єр-міністр",
        "Міністр",
        "Перший заступник міністра",
        "Заступник міністра",
        "Керівник",
        "в.о. керівника",
        "Перший заступник керівника",
        "Заступник керівника",
        "Народний депутат",
        "Голова",
        "Заступник Голови",
        "Перший заступник Голови",
        "Член Правління",
        "Член Ради",
        "Суддя",
        "Член",
        "Генеральний прокурор",
        "Заступник Генерального прокурора",
        "Прокурор області",
        "Військовий прокурор",
        "Надзвичайний і повноважний посол",
        "Головнокомандувач",
        "Службовець першої категорії посад",
        "Член центрального статутного органу",
        "Повірений у справах",
        "Засновник",
        "Учасник",
        "Власник",
        "Колишній засновник/учасник",
        "Бенефіціарний власник",
        "Номінальний власник",
        "Номінальний директор",
        "Директор",
        "в.о директора",
        "Генеральний директор",
        "в.о. генерального директора",
        "Начальник",
        "в.о. начальника",
        "Министр",
        "в.о. министра",
        "в.о. голови",
        "Ліквідатор",
        "Керуючий",
        "Фінансові зв'язки",
        "Секретар",
        "Контролер",
        "Клієнт",
        "Клієнт банку",
    ]

    from_person = models.ForeignKey("Person")
    to_company = models.ForeignKey(
        "Company", verbose_name="Компанія або установа",
        related_name="from_persons")

    relationship_type = models.TextField(
        "Тип зв'язку",
        blank=True)

    is_employee = models.BooleanField(
        "Працює(-вав)",
        default=False
    )

    created_from_edr = models.NullBooleanField(
        "Запис створено з інформації ЄДР",
        default=False
    )

    declarations = ArrayField(
        models.IntegerField(),
        verbose_name="Декларації, що підтверджують зв'язок",
        null=True,
        blank=True
    )

    share = models.DecimalField(
        null=True,
        blank=True,
        decimal_places=6,
        max_digits=9,
        verbose_name="Розмір частки (відсотки)"
    )

    def __unicode__(self):
        return "%s (%s)" % (
            self.to_company, self.relationship_type)

    def to_company_dict(self):
        return {
            "relationship_type_uk": self.relationship_type_uk,
            "relationship_type_en": self.relationship_type_en,
            "date_established": self.date_established_human,
            "date_finished": self.date_finished_human,
            "date_confirmed": self.date_confirmed_human,
            "share": self.share,

            "to_company_is_state": self.to_company.state_company,
            "to_company_edrpou": self.to_company.edrpou,
            "to_company_founded": self.to_company.founded_human,
            "to_company_uk": self.to_company.name_uk,
            "to_company_short_uk": self.to_company.short_name_uk,
            "to_company_en": self.to_company.name_en,
            "to_company_short_en": self.to_company.short_name_en
        }

    def to_person_dict(self):
        return {
            "relationship_type_uk": self.relationship_type_uk,
            "relationship_type_en": self.relationship_type_en,
            "date_established": self.date_established_human,
            "date_finished": self.date_finished_human,
            "date_confirmed": self.date_confirmed_human,
            "share": self.share,

            "is_pep": self.from_person.is_pep,
            "person_uk": "%s %s %s" % (
                self.from_person.first_name_uk,
                self.from_person.patronymic_uk,
                self.from_person.last_name_uk),
            "person_en": "%s %s %s" % (
                self.from_person.first_name_en,
                self.from_person.patronymic_en,
                self.from_person.last_name_en),
        }

    def save(self, *args, **kwargs):
        if not self.relationship_type_en:
            t = Ua2EnDictionary.objects.filter(
                term__iexact=lookup_term(self.relationship_type_uk)).first()

            if t and t.translation:
                self.relationship_type_en = t.translation

        super(Person2Company, self).save(*args, **kwargs)

    class Meta:
        verbose_name = "Зв'язок з компанією/установою"
        verbose_name_plural = "Зв'язки з компаніями/установами"
        index_together = ["is_employee", "date_finished", "date_established", "relationship_type_uk"]


class Company2Company(AbstractRelationship):
    _relationships_explained = [
        _("Власник"),
        _("Співвласник"),
        _("Споріднена"),
        _("Засновник"),
        _("Співзасновник"),
        _("Кредитор (фінансовий партнер)"),
        _("Надавач професійних послуг"),
        _("Клієнт"),
        _("Клієнт банку"),
        _("Виконавець"),
        _("Замовник"),
        _("Підрядник"),
        _("Субпідрядник"),
        _("Постачальник"),
        _("Орендар"),
        _("Орендодавець"),
        _("Контрагент"),
        _("Правонаступник"),
        _("Правовласник"),
        _("Материнська компанія"),
        _("Дочірня компанія"),
        _("Член наглядового органу"),
        _("Колишній власник/засновник"),
        _("Колишній співвласник/співзасновник"),
        _("Самостійний структурний підрозділ"),
        _("Головне підприємство"),
        _("Секретар"),
        _("Директор"),
    ]

    _relationships_mapping = {
        _("Власник"): _("Підконтрольна"),
        _("Співвласник"): _("Підконтрольна"),
        _("Колишній власник/засновник"): _("Підконтрольна"),
        _("Колишній співвласник/співзасновник"): _("Підконтрольна"),
        _("Споріднена"): _("Споріднена"),
        _("Засновник"): _("Підконтрольна"),
        _("Співзасновник"): _("Підконтрольна"),
        _("Кредитор (фінансовий партнер)"): _("Боржник, фінансовий партнер"),
        _("Надавач професійних послуг"): _("Отримувач професійних послуг"),
        _("Клієнт"): _("Надавач товарів/послуг"),
        _("Клієнт банку"): _("Банк"),
        _("Виконавець"): _("Замовник"),
        _("Замовник"): _("Виконавець"),
        _("Підрядник"): _("Замовник"),
        _("Субпідрядник"): _("Підрядник"),
        _("Постачальник"): _("Отримувач/покупець"),
        _("Орендар"): _("Орендодавець"),
        _("Орендодавець"): _("Орендар"),
        _("Контрагент"): _("Контрагент"),
        _("Правонаступник"): _("Попередник"),
        _("Правовласник"): _("Об'єкт правовласності"),
        _("Материнська компанія"): _("Дочірня компанія"),
        _("Дочірня компанія"): _("Материнська компанія"),
        _("Член наглядового органу)"): _("Підконтрольна"),
        _("Самостійний структурний підрозділ"): _("Головне підприємство"),
        _("Головне підприємство"): _("Самостійний структурний підрозділ"),
        _("Секретар"): _("Клієнт"),
        _("Директор"): _("Клієнт"),
    }

    from_company = models.ForeignKey("Company", related_name="to_companies")
    to_company = models.ForeignKey("Company", related_name="from_companies")

    relationship_type = models.CharField(
        "Тип зв'язку",
        choices=zip(_relationships_explained,
                    map(_, _relationships_explained)),
        max_length=40,
        blank=True)

    equity_part = models.FloatField(
        "Частка власності (відсотки)", blank=True, null=True)

    @property
    def reverse_relationship_type(self):
        return self._relationships_mapping.get(self.relationship_type)

    def to_dict(self):
        return {
            "date_established": self.date_established_human,
            "date_finished": self.date_finished_human,
            "date_confirmed": self.date_confirmed_human,
            "relationship_type": self.relationship_type,
            "state_company": self.to_company.state_company,
            "company": self.to_company.name
        }

    def to_dict_reverse(self):
        return {
            "date_established": self.date_established_human,
            "date_finished": self.date_finished_human,
            "date_confirmed": self.date_confirmed_human,
            "relationship_type": self.relationship_type,
            "state_company": self.from_company.state_company,
            "company": self.from_company.name
        }

    class Meta:
        verbose_name = "Зв'язок з компанією"
        verbose_name_plural = "Зв'язки з компаніями"


class Person2Country(AbstractRelationship):
    from_person = models.ForeignKey("Person", verbose_name="Персона")
    to_country = models.ForeignKey("Country", verbose_name="Країна")

    relationship_type = models.CharField(
        "Тип зв'язку",
        choices=(
            ("born_in", _("Народився(-лась)")),
            ("registered_in", _("Зареєстрований(-а)")),
            ("lived_in", _("Проживав(-ла)")),
            ("citizenship", _("Громадянин(-ка)")),
            ("business", _("Має зареєстрований бізнес")),
            ("realty", _("Має нерухомість")),
            ("under_sanctions", _("Під санкціями")),
        ),

        max_length=30,
        blank=False)

    def __unicode__(self):
        return "%s у %s" % (
            self.get_relationship_type_display(), self.to_country)

    def to_dict(self):
        return {
            "date_established": self.date_established_human,
            "date_finished": self.date_finished_human,
            "date_confirmed": self.date_confirmed_human,
            "relationship_type": self.relationship_type,
            "to_country_en": self.to_country.name_en,
            "to_country_uk": self.to_country.name_uk
        }

    class Meta:
        verbose_name = "Зв'язок з країною"
        verbose_name_plural = "Зв'язки з країнами"


class Company2Country(AbstractRelationship):
    from_company = models.ForeignKey(
        "Company", verbose_name="Компанія", related_name="from_countries")
    to_country = models.ForeignKey(
        "Country", verbose_name="Країна")

    relationship_type = models.CharField(
        "Тип зв'язку",
        choices=(
            ("registered_in", _("Зареєстрована")),
            ("under_sanctions", _("Під санкціями")),
        ),

        max_length=30,
        blank=False)

    def to_dict(self):
        return {
            "date_established": self.date_established_human,
            "date_finished": self.date_finished_human,
            "date_confirmed": self.date_confirmed_human,
            "relationship_type": self.relationship_type,
            "to_country_en": self.to_country.name_en,
            "to_country_uk": self.to_country.name_uk
        }

    def __unicode__(self):
        return "%s у %s" % (
            self.get_relationship_type_display(), self.to_country)

    class Meta:
        verbose_name = "Зв'язок з країною"
        verbose_name_plural = "Зв'язки з країнами"


class RelationshipProof(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True)
    object_id = models.PositiveIntegerField(null=True)
    content_object = GenericForeignKey("content_type", "object_id")

    proof_title = models.TextField(
        _("Назва документа або посилання"),
        blank=True,
        help_text=_("Наприклад: склад ВР 7-го скликання"),
    )

    proof_document = models.ForeignKey(
        "core.Document",
        verbose_name=_("Файл документа"),
        default=None,
        blank=True,
        null=True,
    )
    proof = models.TextField(_("або посилання"), blank=True)

    def clean(self):
        if self.proof_document is None and not self.proof:
            raise ValidationError(
                {
                    "proof_document": _(
                        "Поле документа або посилання має бути заповнено"
                    ),
                    "proof": _("Поле документа або посилання має бути заповнено"),
                }
            )

        if self.proof_document is not None and self.proof:
            raise ValidationError(
                {
                    "proof_document": _(
                        "Тільки поле документа або посилання має бути заповнено"
                    ),
                    "proof": _(
                        "Тільки поле документа або посилання має бути заповнено"
                    ),
                }
            )

    def __unicode__(self):
        return "%s: %s" % (self.proof_title, self.proof_document or self.proof)

    class Meta:
        verbose_name = _("Посилання або документ")
        verbose_name_plural = _("Посилання або документи")