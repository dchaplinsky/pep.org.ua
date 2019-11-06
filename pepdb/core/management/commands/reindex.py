# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.core.management.base import BaseCommand
from django.utils.translation import activate
from django.conf import settings

from elasticsearch_dsl import Index
from elasticsearch.helpers import streaming_bulk
from elasticsearch_dsl.connections import connections
from tqdm import tqdm

from core.models import Company, Person
from core.elastic_models import (
    Person as ElasticPerson,
    Company as ElasticCompany,
    person_idx, company_idx
)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '--drop_indices',
            action='store_true',
            dest='drop_indices',
            default=False,
            help='Delete indices before reindex',
        )

    def bulk_write(self, conn, docs_to_index):
        for response in streaming_bulk(
                conn, (d.to_dict(True) for d in docs_to_index), max_retries=2, chunk_size=200):
            pass

    def handle(self, *args, **options):
        activate(settings.LANGUAGE_CODE)
        conn = connections.get_connection('default')

        person_qs = Person.objects.filter(publish=True)
        docs_to_index = [
            ElasticPerson(**p.to_dict())
            for p in tqdm(person_qs.nocache().iterator(), total=person_qs.count())
        ]

        if options["drop_indices"]:
            person_idx.delete(ignore=404)
            person_idx.create()

            ElasticPerson.init()

            conn.indices.put_settings(
                index=ElasticPerson._doc_type.index,
                body={
                    'index.max_result_window': settings.ES_MAX_RESULT_WINDOW,
                }
            )

        self.bulk_write(conn, docs_to_index)

        if options["drop_indices"]:
            # invalidate old values and immediatelly cache again
            ElasticPerson.get_all_persons.invalidate(ElasticPerson)
            ElasticPerson.get_all_persons()

        self.stdout.write(
            'Loaded {} persons to persistence storage'.format(
                len(docs_to_index)))

        company_qs = Company.objects.filter(publish=True)
        docs_to_index = [
            ElasticCompany(**p.to_dict())
            for p in tqdm(company_qs.nocache().iterator(), total=company_qs.count())]

        if options["drop_indices"]:
            company_idx.delete(ignore=404)
            company_idx.create()

            ElasticCompany.init()
            conn.indices.put_settings(
                index=ElasticCompany._doc_type.index,
                body={
                    'index.max_result_window': settings.ES_MAX_RESULT_WINDOW,
                }
            )

        self.bulk_write(conn, docs_to_index)

        if options["drop_indices"]:
            # invalidate old values and immediatelly cache again
            ElasticCompany.get_all_companies.invalidate(ElasticCompany)
            ElasticCompany.get_all_companies()

        self.stdout.write(
            'Loaded {} companies to persistence storage'.format(
                len(docs_to_index)))
