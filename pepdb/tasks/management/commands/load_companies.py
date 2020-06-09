# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re
from random import randrange
import requests
import os.path
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ParseError
import logging
from io import TextIOWrapper, open
from unicodecsv import DictReader
from itertools import islice
from zipfile import ZipFile
from cStringIO import StringIO

from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone

from elasticsearch_dsl import Index
from elasticsearch_dsl.connections import connections
from elasticsearch.helpers import bulk
from dateutil.parser import parse


from tasks.elastic_models import EDRPOU


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("reader")


class EDRImportException(Exception):
    pass


class EDR_Reader(object):
    """
    Simple reader class which allows to iterate over Zipped/not Zipped XML/CSV file
    """

    def __init__(self, in_file, timestamp, revision, file_type="zip"):
        """
        Initializes EDR_Reader class

        :param in_file: file object (zipped or not)
        :type in_file: StringIO or file handler
        :param timestamp: date of export of the file
        :type timestamp: datetime
        :param revision: revision of the dump
        :type revision: string
        :param file_type: type of the file (usually extension)
        :type file_type: string
        """

        self.file = in_file
        self.file_type = file_type
        self.timestamp = timestamp
        self.revision = revision

    def iter_docs(self):
        """
        Reads input file record by record.

        :returns: iterator over company records from registry
        :rtype: collections.Iterable[dict]
        """

        if self.file_type == "zip":
            with ZipFile(self.file) as zip_arch:
                for fname in zip_arch.namelist():
                    try:
                        dec_fname = unicode(fname)
                    except UnicodeDecodeError:
                        dec_fname = fname.decode("cp866")

                    if "uo" in dec_fname.lower() or "юо" in dec_fname.lower():
                        logger.info("Reading {} file from archive {}".format(dec_fname, self.file))

                        if dec_fname.lower().endswith(".xml"):
                            with zip_arch.open(fname, 'r') as fp_raw:
                                for l in self._iter_xml(fp_raw):
                                    yield EDRPOU(**l).to_dict(True)

                        if dec_fname.lower().endswith(".csv"):
                            with zip_arch.open(fname, 'r') as fp_raw:
                                for l in self._iter_csv(fp_raw):
                                    yield EDRPOU(**l).to_dict(True)
        elif self.file_type == "xml":
            for l in self._iter_xml(self.file):
                yield EDRPOU(**l).to_dict(True)

        elif self.file_type == "csv":
            for l in self._iter_csv(self.file):
                yield EDRPOU(**l).to_dict(True)

    def _iter_xml(self, fp_raw):
        """
        Regex magic is required to
        cover records that was incorrectly exported and incomplete, thus
        make whole XML file invalid (happens sometime)
        """

        with TextIOWrapper(fp_raw, encoding="cp1251") as fp:
            mapping = {
                'NAME': 'name',
                'SHORT_NAME': 'short_name',
                'EDRPOU': 'edrpou',
                'ADDRESS': 'location',
                'BOSS': 'head',
                'KVED': 'company_profile',
                'STAN': 'status',
                'FOUNDERS': 'founders',

                "Найменування": 'name',
                "Скорочена_назва": 'short_name',
                "Код_ЄДРПОУ": 'edrpou',
                "Місцезнаходження": 'location',
                "ПІБ_керівника": 'head',
                "Основний_вид_діяльності": 'company_profile',
                "Стан": 'status',
                "C0": ""
            }

            content = fp.read()
            if "RECORD" in content[:1000]:
                regex = '<RECORD>.*?</RECORD>'
            else:
                regex = '<ROW>.*?</ROW>'

            for i, chunk in enumerate(re.finditer(regex, content, flags=re.S | re.U)):
                company = {}
                founders_list = []
                try:
                    # Fucking ET!
                    etree = ET.fromstring(chunk.group(0).replace("Місцезнаходження", "ADDRESS").encode("utf-8"))
                except ParseError:
                    logger.error('Cannot parse record #{}, {}'.format(i, chunk))
                    continue

                for el in etree.getchildren():
                    if el.tag == 'EDRPOU' and el.text and el.text.lstrip('0'):
                        company[mapping[el.tag]] = int(el.text)
                    elif el.tag == 'FOUNDERS':
                        for founder in el.getchildren():
                            founders_list.append(founder.text)
                    else:
                        if el.tag in mapping:
                            company[mapping[el.tag]] = el.text

                company[mapping['FOUNDERS']] = founders_list
                company["last_update"] = self.timestamp
                company["file_revision"] = self.revision

                if i and i % 50000 == 0:
                    logger.warning('Read {} companies from XML feed'.format(i))

                yield company

    def _iter_csv(self, fp_raw):
        r = DictReader(fp_raw, delimiter=str(";"), encoding="cp1251")

        mapping = {
            "Найменування": 'name',
            "Скорочена назва": 'short_name',
            "Код ЄДРПОУ": 'edrpou',
            "Місцезнаходження": 'location',
            "ПІБ керівника": 'head',
            "Основний вид діяльності": 'company_profile',
            "Стан": 'status',
        }

        for i, chunk in enumerate(r):
            company = {}

            for k, v in chunk.items():
                if k.strip():
                    if mapping[k] == "edrpou" and v:
                        company[mapping[k]] = int(v)
                    else:
                        company[mapping[k]] = v

            company['founders'] = []
            company["last_update"] = self.timestamp
            company["file_revision"] = self.revision

            if i and i % 50000 == 0:
                logger.warning('Read {} companies from CSV feed'.format(i))

            yield company


class Command(BaseCommand):
    help = ('Loads XML with data from registry of companies of Ukraine into '
            'elastic index for further matching with companies in DB')

    def add_arguments(self, parser):
        parser.add_argument(
            '--revision',
            help='EDR dump revision to retrieve (leave empty to retrieve latest)',
        )

        parser.add_argument(
            '--guid',
            default="06bbccbd-e19c-40d5-9e18-447b110c0b4c",
            help='Dataset to retrieve',
        )

        parser.add_argument(
            '--filename',
            help='Filename of the dump to load file manually',
        )

        parser.add_argument(
            '--dump_date',
            help='Date of dump, obtained manually, day first',
        )

    def handle(self, *args, **options):
        self.proxies = {}
        if hasattr(settings, "PROXY"):
            self.proxies["http"] = settings.PROXY
            self.proxies["https"] = settings.PROXY

        GUID = options["guid"]
        fp = None
        if not options["revision"]:
            latest = EDRPOU.search().aggs.metric("max_last_update", "max", field="last_update")[:1].execute()
            if latest:
                update_after = latest[0].last_update
                self.stdout.write("Only loading dumps after {}".format(update_after))
            else:
                raise EDRImportException("Current index is empty, please run manual import. For fuck sake")

        if not options["filename"]:
            data_url = None
            timestamp = None
            revision = None

            try:
                response = requests.get(
                    "https://data.gov.ua/api/3/action/resource_show",
                    {"id": GUID, "nocache": randrange(100)}
                ).json()

                if not response.get("success"):
                    self.stderr.write("Unsuccessful response from api.")
                    return

                revisions = sorted(
                    response["result"]["resource_revisions"],
                    key=lambda x: parse(x["resource_created"])
                )

                for rev in revisions:
                    revision = rev["url"].strip("/").rsplit('/', 1)[-1]

                    if not options["revision"]:
                        timestamp = parse(rev["resource_created"])
                        
                        if update_after is None or update_after < timestamp:
                            data_url = rev["url"]
                            break

                    if revision == options["revision"]:
                        timestamp = parse(rev["resource_created"])
                        data_url = rev["url"]
                        break

            except (TypeError, IndexError, KeyError):
                self.stderr.write("Cannot obtain information about dump file")
                raise

            if not data_url:
                self.stderr.write("Can not get dataset url from api.")
                return

            self.stdout.write("Loading data of revision: {}, created at: {}".format(revision, timestamp))

            r = requests.get(data_url, stream=True)

            ext = r.headers["Content-Type"].split("/")[-1]
            ext = ext.lower().lstrip(".")
            if ext not in ["zip", "xml", "csv"]:
                self.stderr.write("Unsupported dataset file type: {}".format(ext))
                return

            reader = EDR_Reader(StringIO(r.content), timestamp, revision, ext)
        elif options["revision"] and options["dump_date"]:
            dump_date = timezone.make_aware(parse(options["dump_date"], dayfirst=True))
            _, ext = os.path.splitext(options["filename"])

            fp = open(options["filename"], "rb")
            reader = EDR_Reader(fp, dump_date, options["revision"], ext.lower().lstrip("."))
        else:
            self.stderr.write("You should provide (possibly fake) revision id and date of dump when loading files manually")

        iterator = reader.iter_docs()

        first_portion = list(islice(iterator, 1000))
        if first_portion:
            Index(EDRPOU._doc_type.index).delete(ignore=404)
            EDRPOU.init()
            es = connections.get_connection()

            bulk(es, first_portion)
            bulk(es, iterator, chunk_size=10000)
        else:
            raise EDRImportException("Less than 1000 valid records, for fuck sake")

        if fp:
            fp.close()
