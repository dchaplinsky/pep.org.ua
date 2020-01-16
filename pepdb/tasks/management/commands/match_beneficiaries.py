# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import re
import json
import logging

from django.core.management.base import BaseCommand
from django.utils.translation import activate
from django.conf import settings

from elasticsearch_dsl import Q

from dateutil.parser import parse as dt_parse
from core.models import Declaration, Person, Company
from core.model.exc import CannotResolveRelativeException
from tasks.elastic_models import EDRPOU
from tasks.models import BeneficiariesMatching
from tasks.constants import COUNTRIES

import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = """
    Collect companies where pep persons are beneficiary owners, clean it up,
    reconcile with companies registry, create tasks for manual verification
    """

    def _search_db(self, company):
        try:
            # Search by code first
            company_db = Company.objects.deep_get(
                [
                    (
                        "edrpou__iexact",
                        (company["beneficial_owner_company_code"] or "").replace(
                            " ", ""
                        ),
                    )
                ]
            )
        except (Company.DoesNotExist, Company.MultipleObjectsReturned):
            try:
                # Then refine the search if needed
                company_db = Company.objects.deep_get(
                    [
                        ("name_uk__iexact", company["company_name"]),
                        ("name_uk__iexact", company["en_name"]),
                        ("name_en__iexact", company["company_name"]),
                        ("name_en__iexact", company["en_name"]),
                    ]
                )

            except Company.DoesNotExist:
                return None
            except Company.MultipleObjectsReturned:
                self.stderr.write(
                    "Too much companies returned for record '%s'"
                    % json.dumps(company, ensure_ascii=False)
                )
                return None

        return {
            "id": company_db.id,
            "code": company_db.edrpou,
            "name_uk": company_db.name_uk,
            "name_en": company_db.name_en,
        }

    def _search_edr(self, company, fuzziness):
        ans = None
        if company["beneficial_owner_company_code"]:
            res = EDRPOU.search().query(
                "term", edrpou=company["beneficial_owner_company_code"].lstrip("0")
            )
            ans = res.execute()
            if not ans:
                self.stdout.write(
                    "Cannot find a company by code %s, falling back to search by name %s"
                    % (
                        company["beneficial_owner_company_code"],
                        company["company_name"],
                    )
                )

        if not ans:
            should = [
                Q(
                    "multi_match",
                    query=company["company_name"],
                    fuzziness=fuzziness,
                    fields=["name", "short_name", "location"],
                    boost=2.0,
                )
            ]

            if company["address"]:
                should.append(
                    Q(
                        "match",
                        location={"query": company["address"], "fuzziness": fuzziness},
                    )
                )

            res = (
                EDRPOU.search()
                .query(Q("bool", should=should))
                .highlight_options(
                    order="score",
                    fragment_size=500,
                    number_of_fragments=100,
                    pre_tags=['<u class="match">'],
                    post_tags=["</u>"],
                )
                .highlight("name", "short_name", "location")
            )

            ans = res.execute()

        return ans

    def search_me(self, ownership, fuzziness=1, candidates=10):
        matches = []
        edrpous_found = []
        ids_found = []

        for company in ownership.pep_company_information:
            # For foreign companies we are searching in PEP database itself
            # for those records that has been imported manually

            if company["country"] != "Україна":
                # Totally different logic of search
                rec = self._search_db(company)

                if rec and rec["id"] not in ids_found:
                    matches.append(rec)
                    ids_found.append(rec["id"])
            else:
                # For ukrainian companies we are searching for the information
                # in our local copy of public EDR
                ans = self._search_edr(company, fuzziness)

                for a in ans[:candidates]:
                    highlight = getattr(a.meta, "highlight", {})

                    name = (
                        " ".join(a.meta.highlight.name)
                        if "name" in highlight
                        else a.name
                    )
                    short_name = (
                        " ".join(a.meta.highlight.short_name)
                        if "short_name" in highlight
                        else a.short_name
                    )
                    location = (
                        " ".join(a.meta.highlight.location)
                        if "location" in highlight
                        else a.location
                    )

                    rec = {
                        "name": name,
                        "short_name": short_name,
                        "location": location,
                        "head": a.head,
                        "edrpou": a.edrpou,
                        "status": a.status,
                        "company_profile": a.company_profile,
                        "score": a._score,
                    }

                    if rec["edrpou"] not in edrpous_found:
                        matches.append(rec)
                        edrpous_found.append(rec["edrpou"])

        return matches[:candidates]

    def resolve_person(self, declaration, person_declaration_id):
        try:
            person, _ = declaration.resolve_person(person_declaration_id)
            return person.pk
        except CannotResolveRelativeException as e:
            self.stderr.write(unicode(e))

    def get_key(self, obj, declarant):
        company_name = re.sub(
            "[\s%s]+" % (re.escape("'\"-.,№()")), "", obj["company_name"].lower(), re.U
        )

        return "!!".join((declarant.full_name, company_name))

    def insert_record(self, obj, declaration, type_of_connection):
        if obj["declarant_id"] is None:
            return

        declarant = Person.objects.get(pk=obj["declarant_id"])
        key = self.get_key(obj, declarant)

        try:
            rec = BeneficiariesMatching.objects.get(
                company_key=key, type_of_connection=type_of_connection
            )

            if obj["country"] != "Україна" and rec.status not in ["y", "n"]:
                self.stderr.write(
                    "Same company %s listed in different sources as domestic and foreign!"
                    % key
                )

        except BeneficiariesMatching.DoesNotExist:
            rec = BeneficiariesMatching(company_key=key, pep_company_information=[])

            if obj["country"] != "Україна":
                rec.status = "n"

        rec.person = obj["declarant_id"]
        rec.type_of_connection = type_of_connection
        rec.person_json = declarant.to_dict()
        rec.is_family_member = obj["owner"] == "FAMILY"
        rec.declarations = list(set(rec.declarations or []) | set([declaration.pk]))

        if obj not in rec.pep_company_information:
            rec.pep_company_information.append(obj)

        if rec.status not in ["y", "m"]:
            rec.candidates_json = {}
        rec.save()

    def add_arguments(self, parser):
        parser.add_argument(
            "--type",
            choices=["beneficiary", "founder", "stakeholder"],
            required=True,
            help="Which type of connection to use",
        )

    def handle(self, *args, **options):
        activate(settings.LANGUAGE_CODE)

        if options["type"] == "beneficiary":
            type_of_connection = "b"
            section = "step_9"
            code_field = "beneficial_owner_company_code"
        elif options["type"] == "founder":
            type_of_connection = "f"
            section = "step_8"
            code_field = "corporate_rights_company_code"
        elif options["type"] == "stakeholder":
            type_of_connection = "s"
            section = "step_7"
            code_field = "emitent_ua_company_code"

        overrides = {
            "ua_company_name_beneficial_owner": "name",
            "address_beneficial_owner": "address",
            "company_name_beneficial_owner": "name",
            "en_company_name_beneficial_owner": "en_name",
            "ua_company_address_beneficial_owner": "address",
            "en_company_address_beneficial_owner": "en_address",
            "company_code_beneficial_owner": code_field,
            "ua_company_code_beneficial_owner": code_field,
        }

        self.stdout.write("Retrieving ownership information")
        for d in (
            Declaration.objects.filter(nacp_declaration=True, confirmed="a")
            .select_related("person")
            .nocache()
            .iterator()
        ):
            data = d.source["nacp_orig"]

            if isinstance(data.get(section), dict):
                for ownership in data[section].values():
                    if not isinstance(ownership, dict):
                        self.stderr.write(
                            "Ownership record '%s' is invalid" % ownership
                        )
                        continue

                    for k, target in overrides.items():
                        if ownership.get(k):
                            ownership[target] = ownership[k]

                    ownership_person = ownership.get("person")
                    if isinstance(ownership_person, dict):
                        if len(ownership_person) == 1:
                            ownership_person = ownership_person.keys()[0]
                        else:
                            logger.error(
                                "Too much ownership records ({}) in declaration {}".format(
                                    len(ownership_person), d.declaration_id
                                )
                            )
                            continue

                    base_rec = {
                        "declarant_id": (
                            d.person_id
                            if ownership_person == "1"
                            else self.resolve_person(d, ownership_person)
                        ),
                        "declarant_name": d.person.full_name,
                        "company_name": ownership.get("name"),
                        "legalForm": ownership.get("legalForm"),
                        "country": COUNTRIES[ownership.get("country", "1") or "1"],
                        "en_name": ownership.get("en_name"),
                        "location": ownership.get("location"),
                        "en_address": ownership.get("en_address"),
                        "phone": ownership.get("phone"),
                        "address": ownership.get("address"),
                        "mail": ownership.get("mail"),
                        "year_declared": d.year,
                        "is_fixed": d.source["intro"].get("corrected", False),
                        "beneficial_owner_company_code": ownership.get(code_field),
                        "owner": "DECLARANT"
                        if ownership.get("person") == "1"
                        else "FAMILY",
                    }

                    if options["type"] == "founder":
                        rights = ownership.get("rights", {}) or {}

                        # Adding all family members declared as coowners/cofounders
                        for person_declaration_id, right in rights.items():
                            person = self.resolve_person(d, person_declaration_id)

                            if person:
                                rec = base_rec.copy()

                                link_type = right.get("otherOwnership") or right.get(
                                    "ownershipType"
                                )

                                # If declarant specified himself in co-owners but forget to specify the share
                                # we'll grab that value from the ownership record
                                percent_of_cost = right.get("percent-ownership")
                                if percent_of_cost:
                                    rec["percent_of_cost"] = str(
                                        percent_of_cost
                                    ).replace(",", ".")
                                elif person_declaration_id == ownership.get("person"):
                                    rec["percent_of_cost"] = str(
                                        ownership.get("cost_percent", "100.")
                                    ).replace(",", ".")

                                if not link_type:
                                    self.stderr.write(
                                        "Cannot determine type of ownership in the record %s"
                                        % (json.dumps(ownership, ensure_ascii=False))
                                    )
                                    link_type = "Співвласник"

                                rec["link_type"] = link_type

                                self.insert_record(
                                    rec,
                                    declaration=d,
                                    type_of_connection=type_of_connection,
                                )

                        # Ignoring ownership record if declarant already specified his ownership rights
                        if ownership.get("person") not in rights:
                            rec = base_rec.copy()

                            link_type = "Співвласник"
                            rec["link_type"] = link_type
                            rec["percent_of_cost"] = str(
                                ownership.get("cost_percent", "100.")
                            ).replace(",", ".")

                            self.insert_record(
                                rec,
                                declaration=d,
                                type_of_connection=type_of_connection,
                            )
                    elif options["type"] == "beneficiary":
                        rec = base_rec.copy()
                        rec["link_type"] = "Бенефіціарний власник"

                        try:
                            self.insert_record(
                                rec,
                                declaration=d,
                                type_of_connection=type_of_connection,
                            )
                        except AttributeError as e:
                            self.stderr.write(
                                "Problem with declaration {}: {}".format(d, str(e))
                            )
                            raise
                    else:
                        rec = base_rec.copy()
                        rec["link_type"] = "Акціонер"

                        rec["company_name"] = ownership.get(
                            "emitent_ua_company_name"
                        ) or ownership.get("emitent_ukr_company_name")

                        rec["en_name"] = ownership.get("emitent_eng_company_name")
                        rec["en_address"] = ownership.get("emitent_eng_company_address")
                        rec["address"] = ownership.get("emitent_ukr_company_address")
                        if ownership.get("owningDate"):
                            rec["owning_date"] = dt_parse(
                                ownership.get("owningDate"), dayfirst=True
                            )
                        rec["cost"] = ownership.get("cost")
                        rec["amount"] = ownership.get("amount")

                        rec["beneficial_owner_company_code"] = ownership.get(
                            code_field
                        ) or ownership.get("emitent_eng_company_code")

                        self.insert_record(
                            rec, declaration=d, type_of_connection=type_of_connection
                        )

        self.stdout.write("Matching with EDR registry")
        for ownership in BeneficiariesMatching.objects.filter(
            status__in=["p", "n"], type_of_connection=type_of_connection
        ):
            candidates = self.search_me(ownership)
            ownership.candidates_json = candidates

            # corner case for foreign companies: here we found a match
            # for a foreign company in PEP db
            if candidates and ownership.status == "n":
                # So switch status to represent that we've found it
                ownership.status = "y"

            ownership.save()
