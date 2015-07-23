# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from unicodecsv import DictReader
from translitua import translitua
from hashlib import sha1

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User

from core.utils import expand_gdrive_download_url, download, title, parse_date
from core.models import Company, Person, Person2Company, Document


class Command(BaseCommand):
    args = '<file_path>'
    help = ('Loads the CSV table of PEPs to db')

    def handle(self, *args, **options):
        try:
            file_path = args[0]
        except IndexError:
            raise CommandError('First argument must be a source file')

        peklun = User.objects.get(username="peklun")

        with open(file_path, 'r') as source:
            r = DictReader(source, errors="ignore")

            for i, l in enumerate(r):
                self.stdout.write(
                    'Processing line #{}'.format(i))

                company_ipn = l.get("ІПН", "")
                company_name = l.get("Назва", "")

                company = None

                if not company_ipn and not company_name:
                    continue
		
		if len(company_name) > 250:
                    continue

                # Search by IPN first (if it's present)
                if company_ipn:
                    try:
                        company = Company.objects.get(edrpou=company_ipn)
                    except Company.DoesNotExist:
                        pass

                # then search by name (if it's present)
                if company_name:
                    if company is None:
                        try:
                            company = Company.objects.get(
                                name=company_name)
                        except Company.DoesNotExist:
                            pass

                if company is None:
                    company = Company(state_company=True)

                # Set missing params
                if not company.name:
                    company.name = company_name

                if not company.edrpou:
                    company.edrpou = company_ipn

                company.save()

                person_name = l.get("ПІБ", "").strip()
                position = l.get("Посада", "").strip()
                person_dob = l.get("Дата народження", "").strip()
                person_from = l.get("Дата призначення", "").strip()
                person_to = l.get("Дата звільнення", "").strip()

                doc_received = l.get("Дата відповіді", "").strip()
                doc = l.get("Лінк на відповідь", "").strip()
                website = l.get("лінк на сайт", "").strip()

                if person_name:
                    chunks = person_name.split(" ")

                    if len(chunks) == 2:
                        last_name = title(chunks[0])
                        first_name = title(chunks[1])
                    elif len(chunks) == 1:
			continue
                    else:
                        last_name = title(" ".join(chunks[:-2]))
                        first_name = title(chunks[-2])
                        patronymic = title(chunks[-1])

                    # Kind of get_or_create
                    try:
                        person = Person.objects.get(
                            first_name__iexact=first_name,
                            last_name__iexact=last_name,
                            patronymic__iexact=patronymic
                        )
                    except Person.DoesNotExist:
                        person = Person(
                            first_name=first_name,
                            last_name=last_name,
                            patronymic=patronymic
                        )

                    person.is_pep = True
                    person.type_of_official = 1
                    if person_dob:
                        person.dob = parse_date(person_dob)
                        if len(person_dob) == 4:
                            person.dob_details = 2  # Only year

                        if len(person_dob) > 4 and len(person_dob) < 7:
                            person.dob_details = 1  # month and year

                    person.save()

                    doc_instance = None
                    if doc and "folderview" not in doc \
                            and "drive/#folders" not in doc:
                        doc = expand_gdrive_download_url(doc)
                        doc_hash = sha1(doc).hexdigest()

                        try:
                            doc_instance = Document.objects.get(hash=doc_hash)
                        except Document.DoesNotExist:
                            self.stdout.write(
                                'Downloading file {}'.format(doc))
                            doc_name, doc_san_name, doc_content = download(doc)
                            doc_san_name = translitua(doc_san_name)

                            if doc_name:
                                doc_instance = Document(
                                    name_ua=doc_name,
                                    uploader=peklun,
                                    hash=doc_hash
                                )

                                doc_instance.doc.save(
                                    doc_san_name, ContentFile(doc_content))
                                doc_instance.save()

                    link, created = Person2Company.objects.update_or_create(
                        from_person=person,
                        to_company=company,
                        is_employee=True,
                        date_established=parse_date(person_from),
                        date_finished=parse_date(person_to)
                    )

                    if not link.relationship_type:
                        link.relationship_type = position

                    if doc_instance is not None:
                        link.proof_title = doc_instance.name
                        link.proof = doc_instance.doc.url

                    link.date_confirmed = parse_date(doc_received)
                    if not doc and website:
                        link.proof = website

                    link.save()
