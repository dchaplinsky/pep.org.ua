# coding: utf-8
from __future__ import unicode_literals

import re
import os.path
import datetime
import json
from zipfile import ZipFile
from unicodecsv import DictWriter, DictReader
from cStringIO import StringIO
import requests
import xlsxwriter
from copy import copy
from hashlib import sha1

from django.contrib import admin, messages
from django.db.models import Q, Count
from django.db import models
from django.conf import settings
from django.conf.urls import url
from django.shortcuts import redirect, render
from django.core.urlresolvers import reverse
from django.utils import formats, timezone
from django.forms import widgets
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.contrib.admin.models import LogEntry

from django.utils.encoding import force_str
from django.utils.translation import ugettext_lazy as _
from django.core.files.base import ContentFile

import nested_admin

from elasticsearch_dsl.query import Q as ES_Q

from grappelli_modeltranslation.admin import (
    TranslationAdmin,
    TranslationStackedInline,
    TranslationGenericStackedInline,
)

from core.models import (
    Country,
    Person,
    Company,
    Person2Person,
    Document,
    Person2Country,
    Person2Company,
    Company2Company,
    Company2Country,
    Ua2RuDictionary,
    Ua2EnDictionary,
    FeedbackMessage,
    Declaration,
    DeclarationExtra,
    ActionLog,
    RelationshipProof,
    DeclarationToLink,
    DeclarationToWatch,
    CompanyCategories,
    Rule,
)

from core.forms import EDRImportForm, ForeignImportForm, ZIPImportForm
from core.importers.company import CompanyImporter
from core.importers.company2country import Company2CountryImporter
from core.universal_loggers import MessagesLogger
from django_otp.plugins.otp_totp.admin import TOTPDeviceAdmin
from django_otp.plugins.otp_totp.models import TOTPDevice
from tasks.elastic_models import EDRPOU


def make_published(modeladmin, request, queryset):
    queryset.update(publish=True)


make_published.short_description = "Опублікувати"


def make_unpublished(modeladmin, request, queryset):
    queryset.update(publish=False)


make_unpublished.short_description = "Приховати"


# TODO: refactor to a smaller files
class TranslationNestedStackedInline(
    nested_admin.NestedInlineModelAdminMixin, TranslationStackedInline
):
    if "grappelli" in settings.INSTALLED_APPS:
        template = "nesting/admin/inlines/grappelli_stacked.html"
    else:
        template = "nesting/admin/inlines/stacked.html"


class ProofsInline(
    nested_admin.NestedInlineModelAdminMixin, TranslationGenericStackedInline
):
    if "grappelli" in settings.INSTALLED_APPS:
        template = "nesting/admin/inlines/grappelli_stacked.html"
    else:
        template = "nesting/admin/inlines/stacked.html"

    formset = nested_admin.NestedBaseGenericInlineFormSet
    inline_classes = ("grp-collapse grp-closed",)

    model = RelationshipProof
    extra = 1

    formfield_overrides = {
        models.TextField: {"widget": widgets.Textarea(attrs={"rows": "1"})}
    }

    raw_id_fields = ("proof_document",)
    fields = ("proof_title", ("proof_document", "proof"))
    autocomplete_lookup_fields = {"fk": ["proof_document"]}


class Person2PersonInline(TranslationNestedStackedInline):
    model = Person2Person
    fk_name = "from_person"
    extra = 1
    fields = [
        "from_relationship_type",
        ("to_relationship_type", "to_person"),
        "relationship_details",
        ("date_established", "date_established_details"),
        ("date_finished", "date_finished_details"),
        ("date_confirmed", "date_confirmed_details"),
    ]

    inline_classes = ("grp-collapse grp-closed",)
    classes = ("p2p-block",)

    raw_id_fields = ("to_person",)
    autocomplete_lookup_fields = {"fk": ["to_person"]}

    inlines = [ProofsInline]

    def get_queryset(self, request):
        qs = super(Person2PersonInline, self).get_queryset(request)
        return qs.select_related("to_person")


class Person2PersonBackInline(TranslationNestedStackedInline):
    verbose_name = "Зворотній зв'язок з іншою персоною"
    verbose_name_plural = "Зворотні зв'язки з іншими персонами"
    model = Person2Person
    fk_name = "to_person"
    extra = 0
    max_num = 0

    inlines = [ProofsInline]
    inline_classes = ("grp-collapse grp-closed",)
    classes = ("p2p-block",)

    raw_id_fields = ("from_person",)
    autocomplete_lookup_fields = {"fk": ["from_person"]}

    def get_queryset(self, request):
        qs = super(Person2PersonBackInline, self).get_queryset(request)
        return qs.select_related("from_person")

    fields = [
        ("from_person", "from_relationship_type"),
        "to_relationship_type",
        "relationship_details",
        ("date_established", "date_established_details"),
        ("date_finished", "date_finished_details"),
        ("date_confirmed", "date_confirmed_details"),
    ]


class Person2CountryInline(nested_admin.NestedStackedInline):
    model = Person2Country
    extra = 1
    fields = [
        ("relationship_type", "to_country"),
        ("date_established", "date_established_details"),
        ("date_finished", "date_finished_details"),
        ("date_confirmed", "date_confirmed_details"),
    ]

    inline_classes = ("grp-collapse grp-closed",)
    classes = ("p2country-block",)
    inlines = [ProofsInline]

    raw_id_fields = ("to_country",)
    autocomplete_lookup_fields = {"fk": ["to_country"]}


class Company2CountryInline(nested_admin.NestedTabularInline):
    model = Company2Country
    extra = 1
    fields = [
        "relationship_type",
        "to_country",
        "date_established",
        "date_finished",
        "date_confirmed",
    ]

    inlines = [ProofsInline]
    raw_id_fields = ("to_country",)
    classes = ("c2country-block",)

    autocomplete_lookup_fields = {"fk": ["to_country"]}


class Person2CompanyInline(TranslationNestedStackedInline):
    model = Person2Company
    extra = 1
    fields = [
        ("relationship_type", "is_employee", "to_company"),
        ("share",),
        ("date_established", "date_established_details"),
        ("date_finished", "date_finished_details"),
        ("date_confirmed", "date_confirmed_details"),
    ]

    raw_id_fields = ("to_company",)

    autocomplete_lookup_fields = {"fk": ["to_company"]}

    inline_classes = ("grp-collapse grp-closed",)
    classes = ("p2c-block",)

    inlines = [ProofsInline]

    def get_queryset(self, request):
        qs = super(Person2CompanyInline, self).get_queryset(request)
        return qs.select_related("to_company")


class Company2PersonInline(TranslationNestedStackedInline):
    verbose_name = "Зв'язок з іншою персоною"
    verbose_name_plural = "Зв'язки з іншими персонами"

    model = Person2Company
    fk_name = "to_company"
    extra = 1
    fields = [
        ("relationship_type", "is_employee", "from_person"),
        ("date_established", "date_established_details"),
        ("date_finished", "date_finished_details"),
        ("date_confirmed", "date_confirmed_details"),
    ]

    inline_classes = ("grp-collapse grp-closed",)
    classes = ("p2c-block",)
    inlines = [ProofsInline]

    raw_id_fields = ("from_person",)
    autocomplete_lookup_fields = {"fk": ["from_person"]}

    def get_queryset(self, request):
        qs = super(Company2PersonInline, self).get_queryset(request)
        return qs.select_related("from_person")


class Company2CompanyInline(nested_admin.NestedTabularInline):
    model = Company2Company
    fk_name = "from_company"
    extra = 1
    fields = [
        "relationship_type",
        "to_company",
        "date_established",
        "date_finished",
        "date_confirmed",
        "equity_part",
    ]
    inlines = [ProofsInline]
    classes = ("c2c-block",)

    raw_id_fields = ("to_company",)
    autocomplete_lookup_fields = {"fk": ["to_company"]}

    def get_queryset(self, request):
        qs = super(Company2CompanyInline, self).get_queryset(request)
        return qs.select_related("to_company")


class Company2CompanyBackInline(nested_admin.NestedTabularInline):
    verbose_name = "Зворотній зв'язок з іншою компанією"
    verbose_name_plural = "Зворотні зв'язки з іншими компаніями"

    model = Company2Company
    fk_name = "to_company"
    extra = 1
    fields = [
        "relationship_type",
        "from_company",
        "date_established",
        "date_finished",
        "date_confirmed",
        "equity_part",
    ]

    inlines = [ProofsInline]
    classes = ("c2c-block",)

    raw_id_fields = ("from_company",)
    autocomplete_lookup_fields = {"fk": ["from_company"]}

    def get_queryset(self, request):
        qs = super(Company2CompanyBackInline, self).get_queryset(request)
        return qs.select_related("from_company")


class DeclarationExtraInline(admin.TabularInline):
    verbose_name = "Додаткова інформація про статки"
    verbose_name_plural = "Додаткова інформація про статки"

    model = DeclarationExtra
    extra = 1
    ordering = ("section", "date_confirmed")
    fields = [
        "date_confirmed",
        "date_confirmed_details",
        "section",
        "note",
        "address",
        "country",
    ]


class HasSanctionsListFilter(admin.SimpleListFilter):
    title = _("Під санкціями або слідство")

    parameter_name = "dirtyboy"

    def lookups(self, request, model_admin):
        return (("sanctions", _("Під санкціями")), ("criminal", _("Під слідством")))

    def queryset(self, request, queryset):
        if self.value() == "sanctions":
            return queryset.filter(
                Q(reputation_sanctions_uk__regex=".+")
                | Q(reputation_sanctions_en__regex=".+")
            )
        if self.value() == "criminal":
            return queryset.filter(
                Q(reputation_crimes_uk__regex=".+")
                | Q(reputation_crimes_en__regex=".+")
            )


class NoTranslationPersonFilter(admin.SimpleListFilter):
    title = _("Наявність перекладу")

    # Parameter for the filter that will be used in the URL query.
    parameter_name = "translation"
    fields = [
        "wiki",
        "reputation_assets",
        "reputation_sanctions",
        "reputation_crimes",
        "reputation_manhunt",
        "reputation_convictions",
    ]

    def lookups(self, request, model_admin):
        return (("no", _("Немає")),)

    def queryset(self, request, queryset):
        # to decide how to filter the queryset.
        if self.value() == "no":
            q = Q()
            for field in self.fields:
                q |= (
                    Q(**{field + "_en": ""}) | Q(**{field + "_en" + "__isnull": True})
                ) & ~(
                    Q(**{field + "_uk": ""}) | Q(**{field + "_uk" + "__isnull": True})
                )

            return queryset.filter(q)
        else:
            return queryset


class NoTranslationCompanyFilter(NoTranslationPersonFilter):
    fields = [
        "wiki",
        "other_founders",
        "other_recipient",
        "other_owners",
        "other_managers",
        "bank_name",
        "sanctions",
    ]


class PersonAdmin(nested_admin.NestedModelAdminMixin, TranslationAdmin):
    class Media:
        css = {"all": ("css/admin/person_admin.css",)}

    inlines = (
        Person2PersonInline,
        Person2PersonBackInline,
        Person2CompanyInline,
        Person2CountryInline,
        ProofsInline,
    )

    list_display = (
        "last_name_uk",
        "first_name_uk",
        "patronymic_uk",
        "is_pep",
        "dob",
        "dob_details",
        "type_of_official",
        "terminated",
        "publish",
    )
    readonly_fields = ("names", "last_change", "last_editor", "_last_modified")
    search_fields = ["last_name_uk", "first_name_uk", "patronymic_uk", "names"]
    list_editable = ("dob", "dob_details", "publish")
    list_filter = ("last_editor", HasSanctionsListFilter, NoTranslationPersonFilter)

    actions = [make_published, make_unpublished]

    fieldsets = [
        (
            "Загальна інформація",
            {
                "fields": [
                    "last_name",
                    "first_name",
                    "patronymic",
                    "also_known_as",
                    "is_pep",
                    "type_of_official",
                    "photo",
                    "dob",
                    "dob_details",
                    "city_of_birth",
                    "publish",
                ]
            },
        ),
        (
            "Припинення статусу ПЕП",
            {
                "fields": [
                    "reason_of_termination",
                    "termination_date",
                    "termination_date_details",
                ]
            },
        ),
        (
            "Додаткова інформація",
            {
                "fields": [
                    "wiki",
                    "wiki_draft",
                    "reputation_assets",
                    "risk_category",
                    "names",
                    "inn",
                    "inn_source",
                    "passport",
                    "passport_source",
                ]
            },
        ),
        (
            "Ділова репутація",
            {
                "fields": [
                    "reputation_sanctions",
                    "reputation_crimes",
                    "reputation_manhunt",
                    "reputation_convictions",
                ]
            },
        ),
        ("Остання зміна", {"fields": ["last_change", "last_editor"]}),
    ]

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["person2person_rels"] = json.dumps(
            Person2Person._relationships_explained
        )
        extra_context["person2company_rels"] = json.dumps(
            Person2Company._relationships_explained
        )

        return super(PersonAdmin, self).change_view(
            request, object_id, form_url, extra_context=extra_context
        )

    def add_view(self, request, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["person2person_rels"] = json.dumps(
            Person2Person._relationships_explained
        )
        extra_context["person2company_rels"] = json.dumps(
            Person2Company._relationships_explained
        )

        return super(PersonAdmin, self).add_view(
            request, form_url, extra_context=extra_context
        )


class CompanyAdmin(nested_admin.NestedModelAdminMixin, TranslationAdmin):
    inlines = (
        Company2PersonInline,
        Company2CompanyInline,
        Company2CompanyBackInline,
        Company2CountryInline,
        ProofsInline,
    )

    list_display = (
        "pk_link",
        "name_uk",
        "short_name_uk",
        "edrpou",
        "publish",
        "state_company",
        "legal_entity",
        "status",
        "management",
    )
    list_editable = (
        "name_uk",
        "short_name_uk",
        "edrpou",
        "state_company",
        "legal_entity",
        "status",
        "publish",
    )
    search_fields = ["name_uk", "short_name_uk", "edrpou"]
    readonly_fields = ("last_change", "last_editor", "_last_modified")
    list_display_links = ("pk_link",)
    list_filter = ("last_editor", NoTranslationCompanyFilter)
    actions = [make_published, make_unpublished]

    class Media:
        css = {"all": ("css/admin/company_admin.css", "css/narrow.css")}

    def edr_search(self, request):
        query = request.GET.get("q")

        s = None
        if query:
            s = (
                EDRPOU.search()
                .query(
                    ES_Q(
                        "multi_match",
                        operator="and",
                        query=query,
                        fields=["name", "short_name", "edrpou", "head", "founders"],
                    )
                )[:200]
                .execute()
            )

        return render(
            request,
            "admin/core/company/edr_search.html",
            {"query": query, "search_results": s},
        )

    def edr_export(self, request):
        data = []

        for rec_id in request.POST.getlist("iswear"):
            meta_id = request.POST.get("company_%s_id" % rec_id)
            res = EDRPOU.get(id=meta_id)
            if res:
                rec = res.to_dict()

                if isinstance(rec.get("founders"), list):
                    rec["founders"] = ";;;".join(rec["founders"])
                data.append(rec)

        if not data:
            self.message_user(request, "Нічого експортувати")
            return redirect(reverse("admin:edr_search"))

        fp = StringIO()
        w = DictWriter(fp, fieldnames=data[0].keys())
        w.writeheader()
        w.writerows(data)
        payload = fp.getvalue()
        fp.close()

        response = HttpResponse(payload, content_type="text/csv")

        response[
            "Content-Disposition"
        ] = "attachment; filename=edr_{:%Y%m%d_%H%M}.csv".format(
            datetime.datetime.now()
        )

        response["Content-Length"] = len(response.content)

        return response

    def edr_import(self, request):
        if request.method == "GET":
            return render(
                request,
                "admin/core/company/edr_import.html",
                {"form": EDRImportForm(initial={"is_state_companies": True})},
            )
        if request.method == "POST":
            form = EDRImportForm(request.POST, request.FILES)

            if not form.is_valid():
                return render(
                    request, "admin/core/company/edr_import.html", {"form": form}
                )

            created_records = 0
            updated_records = 0
            r = DictReader(request.FILES["csv"])
            importer = CompanyImporter(logger=MessagesLogger(request))
            for entry in r:
                company, created = importer.get_or_create_from_edr_record(entry)

                if not company:
                    continue

                if created:
                    created_records += 1
                else:
                    updated_records += 1

                company.state_company = company.state_company or form.cleaned_data.get(
                    "is_state_companies", False
                )

                company.save()

            self.message_user(
                request,
                "Створено %s компаній, оновлено %s"
                % (created_records, updated_records),
            )

            return redirect(reverse("admin:core_company_changelist"))

    def unified_foreign_registry_import(self, request):
        if request.method == "GET":
            return render(
                request,
                "admin/core/company/unified_import.html",
                {"form": ForeignImportForm()},
            )
        if request.method == "POST":
            form = ForeignImportForm(request.POST, request.FILES)

            if not form.is_valid():
                return render(
                    request, "admin/core/company/unified_import.html", {"form": form}
                )

            created_records = 0
            updated_records = 0
            r = DictReader(request.FILES["csv"])
            importer = CompanyImporter(logger=MessagesLogger(request))
            conn_importer = Company2CountryImporter(logger=MessagesLogger(request))

            for entry in r:
                company, created = importer.get_or_create_from_unified_foreign_registry(
                    entry
                )

                if not company:
                    continue

                if created:
                    created_records += 1
                else:
                    updated_records += 1

                country_connection, _ = conn_importer.get_or_create(
                    company, entry.get("country", "").strip(), "registered_in"
                )

            self.message_user(
                request,
                "Створено %s компаній, оновлено %s"
                % (created_records, updated_records),
            )

            return redirect(reverse("admin:core_company_changelist"))

    def get_urls(self):
        urls = super(CompanyAdmin, self).get_urls()
        extra_urls = [
            url(
                r"^edr_search/$",
                self.admin_site.admin_view(self.edr_search),
                name="edr_search",
            ),
            url(
                r"^edr_export/$",
                self.admin_site.admin_view(self.edr_export),
                name="edr_export",
            ),
            url(
                r"^edr_import/$",
                self.admin_site.admin_view(self.edr_import),
                name="edr_import",
            ),
            url(
                r"^unified_import/$",
                self.admin_site.admin_view(self.unified_foreign_registry_import),
                name="unified_import",
            ),
        ]
        return extra_urls + urls

    def management(self, obj):
        managers = obj.all_related_persons["managers"]
        return "<br/>".join(
            [
                '<a href="%s" target="_blank">%s</a>'
                % (
                    reverse("admin:core_person_change", args=(person.pk,)),
                    unicode(person),
                )
                for person in managers
            ]
        )

    management.allow_tags = True

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["person2company_rels"] = json.dumps(
            Person2Company._relationships_explained
        )

        self.inlines = list(self.inlines)
        inlines = copy(self.inlines)

        if request.GET.get("lean"):
            self.inlines.remove(Company2PersonInline)

        resp = super(CompanyAdmin, self).change_view(
            request, object_id, form_url, extra_context=extra_context
        )

        self.inlines = inlines

        return resp

    def pk_link(self, obj):
        return render_to_string("admin/core/company/pk_link.html", {"obj": obj})

    pk_link.allow_tags = True

    def add_view(self, request, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["person2company_rels"] = json.dumps(
            Person2Company._relationships_explained
        )

        return super(CompanyAdmin, self).add_view(
            request, form_url, extra_context=extra_context
        )


class CompanyCategoriesAdmin(CompanyAdmin):
    list_display = (
        "name_uk",
        "edrpou",
        "state_company",
        "legal_entity",
        "status",
        "public_office",
        "political_party",
        "state_enterprise",
        "affiliated_with_pep",
        "bank",
        "service_provider",
    )
    list_editable = (
        "state_company",
        "legal_entity",
        "status",
        "public_office",
        "political_party",
        "state_enterprise",
        "affiliated_with_pep",
        "bank",
        "service_provider",
    )
    search_fields = ["name_uk", "short_name_uk", "edrpou"]
    readonly_fields = ("last_change", "last_editor", "_last_modified")
    list_filter = (
        "state_company",
        "legal_entity",
        "status",
        "public_office",
        "political_party",
        "state_enterprise",
        "affiliated_with_pep",
        "bank",
        "service_provider",
    )
    list_display_links = ("name_uk",)

    def set_public_office(self, request, queryset):
        queryset.update(public_office=True)

    set_public_office.short_description = "Відмитити, як держ.орган"

    def set_political_party(self, request, queryset):
        queryset.update(political_party=True)

    set_political_party.short_description = "Відмитити, як партію"

    def set_state_enterprise(self, request, queryset):
        queryset.update(state_enterprise=True)

    set_state_enterprise.short_description = "Відмитити, як держ. власність"

    def set_affiliated_with_pep(self, request, queryset):
        queryset.update(affiliated_with_pep=True)

    set_affiliated_with_pep.short_description = "Відмитити, як пов'язану з ПЕП"

    def set_bank(self, request, queryset):
        queryset.update(bank=True)

    set_bank.short_description = "Відмитити, як банк"

    def set_service_provider(self, request, queryset):
        queryset.update(service_provider=True)

    set_service_provider.short_description = "Відмитити, як надавача професійних послуг"

    actions = [
        set_public_office,
        set_political_party,
        set_state_enterprise,
        set_affiliated_with_pep,
        set_bank,
        set_service_provider,
    ]


class EmptyValueFilter(admin.SimpleListFilter):
    title = _("Наявність перекладу")

    # Parameter for the filter that will be used in the URL query.
    parameter_name = "translation"

    def lookups(self, request, model_admin):
        return (("no", _("Немає")), ("yes", _("Є")))

    def queryset(self, request, queryset):
        # to decide how to filter the queryset.
        if self.value() == "yes":
            return queryset.exclude(Q(translation="") | Q(translation__isnull=True))
        if self.value() == "no":
            return queryset.filter(Q(translation="") | Q(translation__isnull=True))


def export_to_excel(modeladmin, request, queryset):
    output = StringIO()

    workbook = xlsxwriter.Workbook(output)
    ws = workbook.add_worksheet("translations")
    keys = ["term", "translation", "alt_translation"]

    for j, k in enumerate(keys):
        ws.write(0, j, k)

    for i, trans in enumerate(queryset):
        for j, k in enumerate(keys):
            ws.write(i + 1, j, getattr(trans, k))

    workbook.close()
    output.seek(0)
    response = HttpResponse(
        output.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = "attachment; filename=translations.xlsx"

    return response


export_to_excel.short_description = "Експортувати в Excel"


class Ua2RuDictionaryAdmin(admin.ModelAdmin):
    list_display = ("term", "translation", "alt_translation")
    list_editable = ("translation", "alt_translation")

    search_fields = ["term", "translation", "alt_translation"]

    list_filter = (EmptyValueFilter,)
    actions = [export_to_excel]


class Ua2EnDictionaryAdmin(admin.ModelAdmin):
    list_display = ("term", "translation")
    list_editable = ("translation",)

    search_fields = ["term", "translation"]

    list_filter = (EmptyValueFilter,)
    actions = [export_to_excel]


class CountryAdmin(TranslationAdmin):
    list_display = ("name_uk", "name_en", "iso2", "iso3", "is_jurisdiction")


class DocumentAdmin(TranslationAdmin):
    def zip_import(self, request):
        if request.method == "GET":
            return render(
                request,
                "admin/core/document/zip_import.html",
                {"form": ZIPImportForm()},
            )
        if request.method == "POST":
            form = ZIPImportForm(request.POST, request.FILES)

            if not form.is_valid():
                return render(
                    request, "admin/core/document/zip_import.html", {"form": form}
                )

            with ZipFile(request.FILES["zipfile"]) as zip_arch:
                for finfo in zip_arch.infolist():
                    fullname = finfo.filename

                    if fullname.endswith("/"):
                        continue

                    _, fname = os.path.split(fullname)
                    if fname.startswith("._"):
                        continue

                    if finfo.file_size < 2048:
                        continue

                    try:
                        dec_fname = unicode(fname)
                    except UnicodeDecodeError:
                        dec_fname = fname.decode("cp866")

                    fname, ext = os.path.splitext(dec_fname)
                    doc_san_name = fname.decode("utf-8")
                    human_name = re.sub(r"[\s_]+", " ", doc_san_name)
                    doc_san_name = "{}.{}".format(doc_san_name, ext)

                    with zip_arch.open(fullname, "r") as fp:
                        doc_content = fp.read()
                        doc_hash = sha1(doc_content).hexdigest()

                    try:
                        doc_instance = Document.objects.get(hash=doc_hash)
                        self.message_user(
                            request,
                            "Skipping file {} as it already exists".format(
                                doc_san_name
                            ),
                            level=messages.WARNING,
                        )
                    except Document.DoesNotExist:
                        self.message_user(
                            request, "Adding file {}".format(doc_san_name)
                        )

                        if doc_san_name:
                            doc_instance = Document(
                                name_uk=human_name, uploader=request.user, hash=doc_hash
                            )

                            doc_instance.doc.save(
                                doc_san_name, ContentFile(doc_content)
                            )

                            doc_instance.guess_doc_type()

            return redirect(reverse("admin:core_document_changelist"))

    def link(self, obj):
        return '<a href="{0}{1}" target="_blank">Лінк</a>'.format(
            settings.MEDIA_URL, obj.doc
        )

    link.allow_tags = True
    link.short_description = "Завантажити"

    list_display = ("pk", "name_uk", "link", "uploader", "uploaded", "doc_type", "doc")
    search_fields = ["name", "doc"]
    list_filter = ["doc_type"]
    list_editable = ("name_uk", "uploader", "doc_type", "doc")

    def get_urls(self):
        urls = super(DocumentAdmin, self).get_urls()
        extra_urls = [
            url(
                r"^zip_import/$",
                self.admin_site.admin_view(self.zip_import),
                name="zip_import",
            )
        ]
        return extra_urls + urls

    def save_model(self, request, obj, form, change):
        if change:
            obj.doc_type_set_manually = True
        else:
            obj.guess_doc_type()

        if obj.doc_type != "other":
            obj.doc_type_set_manually = True

        super(DocumentAdmin, self).save_model(request, obj, form, change)


class FeedbackAdmin(admin.ModelAdmin):
    readonly_fields = ("answered_by",)

    def link_expanded(self, obj):
        return (
            '<a href="{0}" target="_blank">Лінк</a>'.format(obj.link)
            if obj.link
            else ""
        )

    link_expanded.allow_tags = True
    link_expanded.short_description = "Джерело"

    def text_expanded(self, obj):
        return (
            "<strong><sup>*</sup> {0}</strong>".format(obj.text)
            if not obj.read
            else '<span style="font-weight:normal">{0}</span>'.format(obj.text)
        )

    text_expanded.allow_tags = True
    text_expanded.short_description = "Інформація"

    list_display = (
        "text_expanded",
        "person",
        "link_expanded",
        "added",
        "email",
        "contacts",
        "short_answer",
        "answer_added",
        "answered_by",
    )

    def get_queryset(self, request):
        qs = super(FeedbackAdmin, self).get_queryset(request)
        return qs.order_by("-pk")

    def save_model(self, request, obj, form, change):
        if change:
            if obj.short_answer != FeedbackMessage.objects.get(pk=obj.pk).short_answer:
                if not obj.answer_added:
                    obj.answer_added = timezone.now()

                obj.answered_by = request.user

        super(FeedbackAdmin, self).save_model(request, obj, form, change)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        FeedbackMessage.objects.filter(pk=object_id).update(read=True)

        return super(FeedbackAdmin, self).change_view(
            request, object_id, form_url, extra_context=extra_context
        )


class DeclarationBaseAdmin(TranslationAdmin):
    def fullname_decl(self, obj):
        return (
            (
                '<a href="%s" target="_blank">%s %s %s</a>'
                % (obj.url, obj.last_name, obj.first_name, obj.patronymic)
            )
            .replace("  ", " ")
            .strip()
        )

    fullname_decl.short_description = "ПІБ з декларації"
    fullname_decl.admin_order_field = "last_name"
    fullname_decl.allow_tags = True

    def fullname_pep(self, obj):
        return (
            (
                '<a href="%s" target="_blank">%s %s %s</a><br/> %s'
                % (
                    reverse("person_details", kwargs={"person_id": obj.person_id}),
                    obj.person.last_name_uk,
                    obj.person.first_name_uk,
                    obj.person.patronymic_uk,
                    (obj.person.also_known_as_uk or "").replace("\n", " ,"),
                )
            )
            .replace("  ", " ")
            .strip()
        )

    fullname_pep.short_description = "ПІБ з БД PEP"
    fullname_pep.allow_tags = True
    fullname_pep.admin_order_field = "person__last_name_uk"

    def position_decl(self, obj):
        return "%s @ %s, %s" % (obj.position, obj.office, obj.declaration_type)

    position_decl.short_description = "Посада з декларації"

    def position_pep(self, obj):
        last_workplace = obj.person.last_workplace
        if last_workplace and last_workplace["position"] != "Клієнт банку":
            return '%s @ %s,<br/><span style="color: silver">%s</span>' % (
                last_workplace["position"],
                last_workplace["company"],
                obj.person.get_type_of_official_display(),
            )

        return ""

    position_pep.short_description = "Посада з БД PEP"
    position_pep.allow_tags = True

    list_select_related = ("person",)
    list_per_page = 50


def populate_relatives(modeladmin, request, queryset):
    return render(
        request,
        "admin/relatives.html",
        {
            "qs": queryset,
            "referer": request.META.get("HTTP_REFERER"),
            "relations": Person2Person._relationships_explained.keys(),
        },
    )


populate_relatives.short_description = "Створити родичів"


class DeclarationAdmin(DeclarationBaseAdmin):
    readonly_fields = (
        "region",
        "office",
        "year",
        "position",
        "fuzziness",
        "batch_number",
        "first_name",
        "last_name",
        "patronymic",
        "url",
        "nacp_declaration",
        "relatives_populated",
        "source",
    )

    def approve(self, request, queryset):
        queryset.update(confirmed="a")

    approve.short_description = "Опублікувати"

    def reject(self, request, queryset):
        queryset.update(confirmed="r")

    reject.short_description = "Відхилити"

    def doublecheck(self, request, queryset):
        queryset.update(confirmed="c")

    doublecheck.short_description = "На повторну перевірку"

    def get_urls(self):
        urls = super(DeclarationAdmin, self).get_urls()
        return [
            url(
                r"^store_relatives/$",
                self.admin_site.admin_view(self.store_relatives),
                name="store_relatives",
            )
        ] + urls

    def store_relatives(self, request):
        input_formats = formats.get_format_lazy("DATE_INPUT_FORMATS")

        def strptime(value):
            for fmt in input_formats:
                try:
                    return datetime.datetime.strptime(force_str(value), fmt).date()
                except (ValueError, TypeError):
                    continue

        persons_created = 0
        connections_created = 0

        persons_updated = 0
        connections_updated = 0

        for rec_id in request.POST.getlist("iswear"):
            last_name = request.POST.get("person_%s_last_name" % rec_id)
            first_name = request.POST.get("person_%s_first_name" % rec_id)
            patronymic = request.POST.get("person_%s_patronymic" % rec_id)
            base_person_id = request.POST.get("person_%s_id" % rec_id)
            declaration_id = request.POST.get("person_%s_declaration_id" % rec_id)
            relation_from = request.POST.get("person_%s_relation_from" % rec_id)
            relation_to = request.POST.get("person_%s_relation_to" % rec_id)

            dob = strptime(request.POST.get("person_%s_dob" % rec_id))
            dob_details = int(request.POST.get("person_%s_dob_details" % rec_id))

            base_person = Person.objects.get(pk=base_person_id)
            declaration = Declaration.objects.get(pk=declaration_id)

            rcpt_id = request.POST.get("person_%s_rcpt_id" % rec_id)
            rel_id = request.POST.get("person_%s_rel_id" % rec_id)

            if rcpt_id:
                relative = Person.objects.get(pk=int(rcpt_id))

                relative.first_name_uk = first_name
                relative.patronymic_uk = patronymic

                persons_updated += 1
                relative.save()
            else:
                relative = Person.objects.create(
                    first_name_uk=first_name,
                    patronymic_uk=patronymic,
                    last_name_uk=last_name,
                    type_of_official=5,
                    is_pep=False,
                )
                persons_created += 1

            if dob is not None:
                relative.dob = dob
                relative.dob_details = dob_details
                relative.save()

            if rel_id:
                relation = Person2Person.objects.get(pk=int(rel_id))

                relation.declarations = list(
                    set((relation.declarations or []) + [declaration_id])
                )

                if relation.from_person_id == base_person.pk:
                    relation.from_relationship_type = relation_from
                    relation.to_relationship_type = relation_to
                else:
                    relation.from_relationship_type = relation_to
                    relation.to_relationship_type = relation_from

                relation.save()

                connections_updated += 1
            else:
                relation = Person2Person.objects.create(
                    declarations=[declaration.pk],
                    from_person=base_person,
                    to_person=relative,
                    from_relationship_type=relation_from,
                    to_relationship_type=relation_to,
                )

                connections_created += 1

            url = declaration.url + "?source"
            try:
                relation.proofs.get(proof=url)
            except RelationshipProof.DoesNotExist:
                relation.proofs.create(
                    proof=url,
                    proof_title_uk="Декларація за %s рік" % declaration.year,
                    proof_title_en="Income and assets declaration, %s"
                    % declaration.year,
                )
            except RelationshipProof.MultipleObjectsReturned:
                pass

            declaration.relatives_populated = True
            declaration.save()

        self.message_user(
            request,
            "%s осіб та %s зв'язків було створено."
            % (persons_created, connections_created),
        )

        self.message_user(
            request,
            "%s осіб та %s зв'язків було оновлено."
            % (persons_updated, connections_updated),
        )

        if request.POST.get("redirect_back"):
            return redirect(request.POST.get("redirect_back"))
        else:
            return redirect(reverse("admin:core_declaration_changelist"))

    def family_table(self, obj):
        family = obj.family
        if family:
            return "".join(
                [
                    "<strong>Родину вже було внесено до БД</strong>"
                    if obj.relatives_populated
                    else ""
                ]
                + ["<table>"]
                + [
                    (
                        "<tr><td>{name}</td><td>{relation}</td>"
                        + "<td>{mapped}</td</tr>"
                    ).format(**x)
                    for x in family
                    if x
                ]
                + ["</table>"]
            )

        return "<strong>Родини нема</strong>" if obj.relatives_populated else ""

    family_table.short_description = "Родина"
    family_table.allow_tags = True

    list_display = (
        "pk",
        "fullname_pep",
        "fullname_decl",
        "position_pep",
        "position_decl",
        "region",
        "year",
        "family_table",
        "confirmed",
        "fuzziness",
        "batch_number",
    )

    search_fields = [
        "last_name",
        "first_name",
        "patronymic",
        "person__last_name_uk",
        "person__first_name_uk",
        "person__patronymic_uk",
        "declaration_id",
    ]

    raw_id_fields = ("person",)
    autocomplete_lookup_fields = {"fk": ["person"]}

    list_editable = ("confirmed",)
    list_filter = ("confirmed", "relatives_populated", "batch_number")

    actions = [populate_relatives, approve, reject, doublecheck]

    def save_model(self, request, obj, form, change):
        if not change:
            decl = requests.get(
                settings.DECLARATION_DETAILS_ENDPOINT.format(obj.declaration_id),
                params={"format": "json"},
                verify=False,
                timeout=60,
            ).json()["declaration"]

            if "ft_src" in decl:
                del decl["ft_src"]
            if "index_card" in decl:
                del decl["index_card"]

            if decl["id"].startswith("nacp_"):
                if "nacp_src" in decl:
                    del decl["nacp_src"]

                if decl["intro"]["doc_type"] == "Форма змін":
                    return

                # TODO: DRY me
                obj.last_name = decl["general"]["last_name"]
                obj.first_name = decl["general"]["name"]
                obj.patronymic = decl["general"]["patronymic"]
                obj.position_uk = decl["general"]["post"]["post"]
                obj.office_uk = decl["general"]["post"]["office"]
                obj.region_uk = decl["general"]["post"]["region"]
                obj.year = decl["intro"]["declaration_year"]
                obj.source = decl
                obj.batch_number = 100
                obj.nacp_declaration = True
                obj.to_link = True
                obj.url = settings.DECLARATION_DETAILS_ENDPOINT.format(decl["id"])
                obj.fuzziness = 0
            else:
                obj.last_name = decl["general"]["last_name"]
                obj.first_name = decl["general"]["name"]
                obj.patronymic = decl["general"]["patronymic"]
                obj.position_uk = decl["general"]["post"]["post"]
                obj.office_uk = decl["general"]["post"]["office"]
                obj.region_uk = decl["general"]["post"]["region"]
                obj.year = decl["intro"]["declaration_year"]
                obj.source = decl
                obj.batch_number = 100
                obj.to_link = True
                obj.url = settings.DECLARATION_DETAILS_ENDPOINT.format(decl["id"])
                obj.fuzziness = 0

            if not obj.family:
                obj.relatives_populated = True

        super(DeclarationAdmin, self).save_model(request, obj, form, change)


class DeclarationMonitorAdmin(DeclarationBaseAdmin):
    list_filter = ("submitted", "acknowledged")

    list_editable = ("to_link",)

    def make_monitored(self, request, queryset):
        queryset.update(acknowledged=True)

    make_monitored.short_description = "Помітити як оброблене"

    def make_unmonitored(self, request, queryset):
        queryset.update(acknowledged=False)

    make_unmonitored.short_description = "Помітити як необроблене"

    actions = [make_monitored, make_unmonitored]

    list_display = (
        "pk",
        "fullname_pep",
        "fullname_decl",
        "position_pep",
        "position_decl",
        "region",
        "year",
        "fuzziness",
        "acknowledged",
        "to_link",
        "submitted",
    )

    search_fields = [
        "last_name",
        "first_name",
        "patronymic",
        "person__last_name_uk",
        "person__first_name_uk",
        "person__patronymic_uk",
        "declaration_id",
    ]

    def has_add_permission(self, request):
        return False


class ActionLogAdmin(admin.ModelAdmin):
    list_display = ("user", "action", "timestamp", "details")
    ordering = ("-timestamp",)

    list_filter = ("user", "action")
    search_filter = ("user",)

    def has_add_permission(self, request):
        return False


class LogEntryAdmin(admin.ModelAdmin):
    readonly_fields = (
        "content_type",
        "user",
        "action_time",
        "object_id",
        "object_repr",
        "action_flag",
        "change_message",
    )

    list_display = ("__str__", "user", "action_time")
    list_filter = ("user", "action_time")
    search_fields = ("change_message", "object_repr")

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def get_actions(self, request):
        actions = super(LogEntryAdmin, self).get_actions(request)
        del actions["delete_selected"]
        return actions


class RiggedTOTPDeviceAdmin(TOTPDeviceAdmin):
    def get_queryset(self, request):
        qs = super(RiggedTOTPDeviceAdmin, self).get_queryset(request)

        if request.user.is_superuser and request.user.username in settings.SUPERADMINS:
            return qs
        else:
            return qs.filter(user=request.user)


class RelationshipTypeFilter(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _("Фільтр за зв'язком")

    # Parameter for the filter that will be used in the URL query.
    parameter_name = "rel_type"

    def lookups(self, request, model_admin):
        field = "relationship_type_uk"
        return [
            (p2c[field], "{}: {}".format(p2c[field], p2c["type_count"]))
            for p2c in Person2Company.objects.values(field)
            .annotate(type_count=Count(field))
            .order_by("-type_count")
        ]

    def queryset(self, request, queryset):
        field = "relationship_type_uk"
        value = self.value()
        if value:
            return queryset.filter(**{field: value})


class Person2CompanyAdmin(TranslationAdmin):
    class Media:
        css = {"all": ("css/admin/person2company_admin.css",)}

    list_display = [
        "from_person",
        "to_company",
        "relationship_type_uk",
        "is_employee",
        "share",
    ]
    list_editable = ["relationship_type_uk", "is_employee"]
    search_fields = ["relationship_type_uk", "relationship_type_en"]
    list_filter = ("is_employee", RelationshipTypeFilter)

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False


class RuleAdmin(TranslationAdmin):
    list_display = [
        "pk",
        "get_id_display",
        "template_uk",
        "template_en",
        "weight",

    ]

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

admin.site.register(Person, PersonAdmin)
admin.site.register(Company, CompanyAdmin)
admin.site.register(Country, CountryAdmin)
admin.site.register(Document, DocumentAdmin)
admin.site.register(Ua2RuDictionary, Ua2RuDictionaryAdmin)
admin.site.register(Ua2EnDictionary, Ua2EnDictionaryAdmin)
admin.site.register(FeedbackMessage, FeedbackAdmin)
admin.site.register(DeclarationToLink, DeclarationAdmin)
admin.site.register(DeclarationToWatch, DeclarationMonitorAdmin)
admin.site.register(ActionLog, ActionLogAdmin)
admin.site.register(LogEntry, LogEntryAdmin)
admin.site.register(Person2Company, Person2CompanyAdmin)
admin.site.register(CompanyCategories, CompanyCategoriesAdmin)
admin.site.register(Rule, RuleAdmin)

admin.site.unregister(TOTPDevice)
admin.site.register(TOTPDevice, RiggedTOTPDeviceAdmin)

