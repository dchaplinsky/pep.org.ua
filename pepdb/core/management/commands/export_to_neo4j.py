# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import re
import os.path

import csv
from unicodecsv import writer
from tqdm import tqdm
from neomodel import StringProperty, BooleanProperty, IntegerProperty, FloatProperty

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from core.models import (
    Person,
    Company,
    Country,
    Person2Person,
    Company2Company,
    Person2Company,
    Company2Country,
    Person2Country,
)


from core.neo_models import (
    Person as NeoPerson,
    Company as NeoCompany,
    Country as NeoCountry,
    Company2Company as NeoCompany2Company,
    Person2Company as NeoPerson2Company,
    Person2Person as NeoPerson2Person,
)


class Command(BaseCommand):
    neomodel_to_types_mapping = {
        IntegerProperty: "INT",
        StringProperty: "STRING",
        BooleanProperty: "BOOLEAN",
        FloatProperty: "FLOAT",
    }

    def add_arguments(self, parser):
        parser.add_argument("output_dir", help="Directory to export CSVs")

    def norm_str(self, s):
        if isinstance(s, bool):
            return "true" if s else "false"

        return re.sub("\s+", " ", unicode(s).replace("\n", " ").strip())

    def get_field_types(self, neo_model):
        field_types = {}

        if neo_model is not None:
            for prop, cls in neo_model.defined_properties().items():
                field_types[prop] = self.neomodel_to_types_mapping.get(
                    type(cls), "string"
                )

        return field_types

    def export_nodes(self, fname, qs, neo_model=None, labels=[]):
        field_types = self.get_field_types(neo_model)

        self.nodes.append(os.path.basename(fname))
        with open(fname, "w") as fp:
            w = writer(fp, quoting=csv.QUOTE_ALL)
            id_fields = "%sId:ID(%s)" % (qs.model.__name__.lower(), qs.model.__name__)

            first = qs.first()
            fields = list(first.get_node()["data"].keys())

            w.writerow(
                [id_fields]
                + list("{}:{}".format(k, field_types.get(k, "STRING")) for k in fields)
                + [":LABEL"]
            )

            for obj in tqdm(qs.iterator(), total=qs.count()):
                row = [obj.pk]
                node_info = obj.get_node()["data"]

                row += [self.norm_str(node_info[f]) for f in fields]

                row.append(";".join(labels))
                w.writerow(row)

    def export_relations(self, fname, qs, src, dst, neo_model=None):
        field_types = self.get_field_types(neo_model)

        self.relationships.append(os.path.basename(fname))

        with open(fname, "w") as fp:
            w = writer(fp, quoting=csv.QUOTE_ALL)
            if_fld_from = getattr(qs.model, src).field.related_model.__name__
            if_fld_to = getattr(qs.model, dst).field.related_model.__name__

            first = qs.first()
            fields = list(first.get_node()["data"].keys())

            w.writerow(
                [":START_ID(%s)" % if_fld_from, ":END_ID(%s)" % if_fld_to, ":TYPE"]
                + list("{}:{}".format(k, field_types.get(k, "STRING")) for k in fields)
            )

            for obj in tqdm(qs.iterator(), total=qs.count()):
                row = [
                    getattr(obj, src + "_id"),
                    getattr(obj, dst + "_id"),
                    qs.model.__name__,
                ]

                node_info = obj.get_node()["data"]

                row += [self.norm_str(node_info[f]) for f in fields]

                w.writerow(row)

    def handle(self, *args, **options):
        output_dir = options["output_dir"]
        self.relationships = []
        self.nodes = []

        try:
            if not os.path.isdir(output_dir):
                os.makedirs(output_dir)
        except OSError:
            raise CommandError("Cannot create output dir")

        self.export_nodes(
            os.path.join(output_dir, "persons.csv"),
            Person.objects.all().nocache(),
            neo_model=NeoPerson,
            labels=["Person"],
        )

        self.export_nodes(
            os.path.join(output_dir, "companies.csv"),
            Company.objects.all().nocache(),
            neo_model=NeoCompany,
            labels=["Company"],
        )

        self.export_nodes(
            os.path.join(output_dir, "countries.csv"),
            Country.objects.exclude(iso2="").nocache(),
            neo_model=NeoCountry,
            labels=["Country"],
        )

        self.export_relations(
            os.path.join(output_dir, "person2person.csv"),
            Person2Person.objects.all().nocache(),
            "from_person",
            "to_person",
            neo_model=NeoPerson2Person,
        )

        self.export_relations(
            os.path.join(output_dir, "person2company.csv"),
            Person2Company.objects.all().nocache(),
            "from_person",
            "to_company",
            neo_model=NeoPerson2Company,
        )

        self.export_relations(
            os.path.join(output_dir, "company2company.csv"),
            Company2Company.objects.all().nocache(),
            "from_company",
            "to_company",
            neo_model=NeoCompany2Company,
        )

        # self.export_relations(
        #     os.path.join(output_dir, "person2country.csv"),
        #     Person2Country.objects.all().nocache(),
        #     "from_person",
        #     "to_country",
        #     [
        #         "relationship_type",
        #         "date_established_human",
        #         "date_finished_human",
        #         "date_confirmed_human",
        #         "proof_title",
        #         "proof",
        #     ],
        # )

        # self.export_relations(
        #     os.path.join(output_dir, "company2country.csv"),
        #     Company2Country.objects.all().nocache(),
        #     "from_company",
        #     "to_country",
        #     [
        #         "relationship_type",
        #         "date_established_human",
        #         "date_finished_human",
        #         "date_confirmed_human",
        #         "proof_title",
        #         "proof",
        #     ],
        # )

        # with open(os.path.join(output_dir, "neo4j_import.sh"), "w") as fp:
        #     cmd = "{} import --id-type=INTEGER --database={} \\\n"
        #     fp.write(
        #         cmd.format(settings.NEO4J_ADMIN_PATH, settings.NEO4J_DATABASE_NAME)
        #     )
        #     fp.write("\t--multiline-fields=true \\\n")

        #     for node in self.nodes:
        #         cmd = "\t--nodes={} \\\n"
        #         fp.write(cmd.format(node))

        #     for relationship in self.relationships:
        #         cmd = "\t--relationships={} \\\n"
        #         fp.write(cmd.format(relationship))
