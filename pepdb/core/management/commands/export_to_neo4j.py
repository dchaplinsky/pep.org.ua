# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import re
import os.path
from tqdm import tqdm
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
import csv
from unicodecsv import writer
from core.models import (
    Person, Company, Country, Person2Person, Company2Company,
    Person2Company, Company2Country, Person2Country)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            'output_dir',
            help='Directory to export CSVs',
        )

    def norm_str(self, s):
        return re.sub("\s+", " ", unicode(s).replace("\n", " ").strip())

    def export_nodes(self, fname, qs, labels=[]):
        self.nodes.append(os.path.basename(fname))
        with open(fname, "w") as fp:
            w = writer(fp, quoting=csv.QUOTE_ALL)
            id_fields = "%sId:ID(%s)" % (
                qs.model.__name__.lower(), qs.model.__name__)

            first = qs.first()
            fields = list(first.get_node()["data"].keys())

            w.writerow([id_fields] + fields + [":LABEL"])

            for obj in tqdm(qs.iterator(), total=qs.count()):
                row = [obj.pk]
                node_info = obj.get_node()["data"]

                for f in fields:
                    row.append(self.norm_str(node_info[f]))

                row.append(";".join(labels))
                w.writerow(row)

    def export_relations(self, fname, qs, src, dst, fields):
        self.relationships.append(os.path.basename(fname))
        with open(fname, "w") as fp:
            w = writer(fp, quoting=csv.QUOTE_ALL)
            if_fld_from = getattr(qs.model, src).field.related_model.__name__
            if_fld_to = getattr(qs.model, dst).field.related_model.__name__

            w.writerow(
                [
                    ":START_ID(%s)" % if_fld_from,
                    ":END_ID(%s)" % if_fld_to,
                    ":TYPE"
                ] + fields)

            for obj in tqdm(qs.iterator(), total=qs.count()):
                w.writerow(
                    [
                        getattr(obj, src + "_id"),
                        getattr(obj, dst + "_id"),
                        qs.model.__name__
                    ] +
                    [
                        getattr(obj, "get_%s_display" % x)()
                        if hasattr(obj, "get_%s_display" % x) else
                        self.norm_str(getattr(obj, x)) for x in fields
                    ]
                )

    def handle(self, *args, **options):
        output_dir = options["output_dir"]
        self.relationships = []
        self.nodes = []

        try:
            if not os.path.isdir(output_dir):
                os.makedirs(output_dir)
        except OSError:
            raise CommandError('Cannot create output dir')

        self.export_nodes(
            os.path.join(output_dir, "persons.csv"),
            Person.objects.all().nocache(),
            ["Person"]
        )

        self.export_nodes(
            os.path.join(output_dir, "companies.csv"),
            Company.objects.all().nocache(),
            ["Company"]
        )

        self.export_nodes(
            os.path.join(output_dir, "countries.csv"),
            Country.objects.exclude(iso2="").nocache(),
            ["Country"]
        )

        self.export_relations(
            os.path.join(output_dir, "person2person.csv"),
            Person2Person.objects.all().nocache(),
            "from_person",
            "to_person",
            [
                "from_relationship_type",
                "to_relationship_type",
                "date_established_human",
                "date_finished_human",
                "date_confirmed_human",
                "proof_title",
                "proof",
            ]
        )

        self.export_relations(
            os.path.join(output_dir, "person2company.csv"),
            Person2Company.objects.all().nocache(),
            "from_person",
            "to_company",
            [
                "relationship_type",
                "is_employee",
                "date_established_human",
                "date_finished_human",
                "date_confirmed_human",
                "proof_title",
                "proof",
            ]
        )

        self.export_relations(
            os.path.join(output_dir, "company2company.csv"),
            Company2Company.objects.all().nocache(),
            "from_company",
            "to_company",
            [
                "relationship_type",
                "reverse_relationship_type",
                "equity_part",
                "date_established_human",
                "date_finished_human",
                "date_confirmed_human",
                "proof_title",
                "proof",
            ]
        )

        self.export_relations(
            os.path.join(output_dir, "person2country.csv"),
            Person2Country.objects.all().nocache(),
            "from_person",
            "to_country",
            [
                "relationship_type",
                "date_established_human",
                "date_finished_human",
                "date_confirmed_human",
                "proof_title",
                "proof",
            ]
        )

        self.export_relations(
            os.path.join(output_dir, "company2country.csv"),
            Company2Country.objects.all().nocache(),
            "from_company",
            "to_country",
            [
                "relationship_type",
                "date_established_human",
                "date_finished_human",
                "date_confirmed_human",
                "proof_title",
                "proof",
            ]
        )

        with open(os.path.join(output_dir, "neo4j_import.sh"), "w") as fp:
            cmd = '{} import --id-type=STRING --database={} \\\n'
            fp.write(cmd.format(settings.NEO4J_ADMIN_PATH, settings.NEO4J_DATABASE_NAME))
            fp.write('\t--multiline-fields=true \\\n')

            for node in self.nodes:
                cmd = '\t--nodes={} \\\n'
                fp.write(cmd.format(node))

            for relationship in self.relationships:
                cmd = '\t--relationships={} \\\n'
                fp.write(cmd.format(relationship))
