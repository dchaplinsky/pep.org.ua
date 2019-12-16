# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import re
import os.path
import requests
import urllib2
import httplib2
from string import capwords
from datetime import datetime, date

from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils import formats
from django.utils.translation import ugettext_lazy, activate, get_language

import gspread
from dateutil import parser, relativedelta
from rfc6266 import parse_requests_response
from oauth2client.client import SignedJwtAssertionCredentials

from core.dicts.rates import UAH_rates

import logging
logger = logging.getLogger(__name__)


def expand_gdrive_download_url(url):
    """
    Convert google drive links like.

    https://drive.google.com/file/d/BLAHBLAH/view?usp=sharing
    to links that can be used for direct download from gdrive with requests
    """
    m = re.search(r"file\/d\/([^\/]+)\/", url)
    if m:
        return "https://docs.google.com/uc?export=download&id=%s" % m.group(1)

    m = re.search(r"open\?id=([^&]+)", url)
    if m:
        return "https://docs.google.com/uc?export=download&id=%s" % m.group(1)

    return url


def download(url, name=""):
    """
    Download from url, extracts filename from url or content disposition.

    Returns original fname, sanitized one and content of file
    Or None, None, None
    """
    resp = requests.get(url)

    if resp.status_code == 200:
        parsed = parse_requests_response(resp)
        if name:
            fname = name + os.path.splitext(parsed.filename_unsafe)[-1]
        else:
            fname = parsed.filename_sanitized(
                os.path.splitext(parsed.filename_unsafe)[-1].strip("."))

        return parsed.filename_unsafe, fname, resp.content
    else:
        return None, None, None


def title(s):
    chunks = s.split()
    chunks = map(lambda x: capwords(x, u"-"), chunks)
    return u" ".join(chunks)


def parse_date(s):
    try:
        s = unicode(s).strip()
        if s == "-" or not s:
            return None

        return parser.parse(s, default=datetime(1970, 1, 1),
                            dayfirst=True).date()
    except ValueError:
        return None


class CSVDownloadClient(object):
    """
    Class to quickly export google spreadsheet into CSV and download it.

    Currently not in use
    """

    def __init__(self, auth_key=getattr(settings, "GAUTH_CREDENTIALS", None)):
        super(CSVDownloadClient, self).__init__()
        self.auth_key = auth_key

    def get_auth_token(self):
        scope = ['https://spreadsheets.google.com/feeds']
        credentials = SignedJwtAssertionCredentials(
            self.auth_key['client_email'], self.auth_key['private_key'], scope)

        credentials.refresh(httplib2.Http())
        return credentials.token_response["access_token"]

    def download(self, spreadsheet=getattr(settings, "SPREADSHEET_ID", None),
                 gid=0, format="csv"):
        url_format = ("https://spreadsheets.google.com/feeds/download/"
                      "spreadsheets/Export?key=%s&exportFormat=%s&gid=%i")
        headers = {
            "Authorization": "Bearer " + self.get_auth_token()
        }
        req = urllib2.Request(url_format % (spreadsheet, format, gid),
                              headers=headers)

        return urllib2.urlopen(req)


def get_spreadsheet(auth_key=getattr(settings, "GAUTH_CREDENTIALS", None),
                    spreadsheet=getattr(settings, "SPREADSHEET_ID", None)):
    """
    Helper to authenticate on google drive and obtain spreadsheet object.
    """
    credentials = SignedJwtAssertionCredentials(
        auth_key['client_email'], auth_key['private_key'],
        ['https://spreadsheets.google.com/feeds'])

    credentials.refresh(httplib2.Http())

    gc = gspread.authorize(credentials)
    return gc.open_by_key(spreadsheet)


def is_cyr(name):
    return re.search("[а-яіїєґ]+", name.lower(), re.UNICODE) is not None


def is_ukr(name):
    return re.search("['іїєґ]+", name.lower(), re.UNICODE) is not None


def is_eng(name):
    return re.search("[a-z]+", name.lower(), re.UNICODE) is not None


def is_greek(name):
    return re.search("[α-ωίϊΐόάέύϋΰήώ]+", name.lower(), re.UNICODE) is not None


def parse_fullname(person_name):
    # Extra care for initials (especialy those without space)
    person_name = re.sub("\s+", " ",
                         person_name.replace(".", ". ").replace('\xa0', " "))

    chunks = person_name.strip().split(" ")

    last_name = ""
    first_name = ""
    patronymic = ""
    dob = ""

    numeric_chunks = list(
        filter(lambda x: re.search("\d+\.?", x), chunks)
    )

    chunks = list(
        filter(lambda x: re.search("\d+\.?", x) is None, chunks)
    )

    if len(chunks) == 2:
        last_name = title(chunks[0])
        first_name = title(chunks[1])
    elif len(chunks) > 2:
        last_name = title(" ".join(chunks[:-2]))
        first_name = title(chunks[-2])
        patronymic = title(chunks[-1])

    if numeric_chunks:
        dob = "".join(numeric_chunks)

    return last_name, first_name, patronymic, dob


class TranslatedField(object):
    def __init__(self, ua_field, en_field):
        self.ua_field = ua_field
        self.en_field = en_field

    def __get__(self, instance, owner):

        if get_language() == 'en':
            return (getattr(instance, self.en_field, "") or
                    getattr(instance, self.ua_field, ""))
        else:
            return getattr(instance, self.ua_field, "")


VALID_POSITIONS = [
    "син",
    "дружина",
    "чоловік",
    "донька",
    "дочка",
    "мати",
    "батько",
    "жінка",
    "брат",
    "дружина брата",
    "сестра",
    "теща",
    "онук",
    "мама",
    "невістка",
    "племінник",
    "баба",
    "пасинок",
    "дитина",
    "матір",
    "онука",
    "зять",
    "діти",
    "свекор",
    "бабуся",
    "племінниця",
    "донечка",
    "тесть",
    "внучка",
    "сын",
    "чоловик",
    "співмешканець",
    "супруга",
    "допька",
    "дружіна",
    "падчерка",
    "внук",
    "свекруха",
    "мать",
    "доч",
    "батьки",
    "тітка",
    "співмешканака",
    "онучка",
    "тато",
    "жена",
]

RELATIONS_MAPPING = {
    "подружжя": "чоловік/дружина",
    "батьки": "батько/мати",
    "дитина": "син/дочка",
    "онук": "внук",
    "брат": "рідний брат",
    "інше": "особисті зв'язки",
    "син": "син",
    "дружина": "дружина",
    "чоловік": "чоловік",
    "донька": "дочка",
    "дочка": "дочка",
    "мати": "мати",
    "батько": "батько",
    "жінка": "дружина",
    "брат": "брат",
    "дружина брата": "особисті зв'язки",
    "сестра": "рідна сестра",
    "теща": "особисті зв'язки",
    "онук": "внук",
    "мама": "мати",
    "невістка": "особисті зв'язки",
    "племінник": "особисті зв'язки",
    "баба": "баба",
    "пасинок": "усиновлений",
    "дитина" "син/дочка"
    "матір": "мати",
    "онука": "внучка",
    "зять": "особисті зв'язки",
    "діти": "син/дочка",
    "свекор": "особисті зв'язки",
    "бабуся": "баба",
    "племінниця": "особисті зв'язки",
    "донечка": "дочка",
    "тесть": "особисті зв'язки",
    "внучка": "внучка",
    "сын": "син",
    "чоловик": "чоловік",
    "співмешканець": "особи, які спільно проживають",
    "супруга": "дружина",
    "допька": "дочка",
    "дружіна": "дружина",
    "падчерка": "усиновлена",
    "внук": "внук",
    "свекруха": "особисті зв'язки",
    "мать": "мати",
    "доч": "дочка",
    "батьки": "батько/мати",
    "тітка": "особисті зв'язки",
    "співмешканака": "особи, які спільно проживають",
    "онучка": "внучка",
    "тато": "батько",
    "жена": "дружина"
}


def parse_family_member(s):
    try:
        position, person = s.split(None, 1)
        if "-" in position:
            position, person = s.split("-", 1)

        position = position.strip(u" -—,.:").lower()
        person = person.strip(u" -—,")

        if position not in VALID_POSITIONS:
            raise ValueError

        for pos in VALID_POSITIONS:
            if person.lower().startswith(pos):
                raise ValueError

        person = re.sub("приховано", "", person, flags=re.I)

        return {
            "relation": position,
            "name": person.strip(" ,")
        }
    except ValueError:
        return None


def render_date(dt, date_details):
    if not dt:
        return ""

    # Date precision = full date
    if date_details == 0:
        return formats.date_format(dt, "SHORT_DATE_FORMAT")
    # Date precision = we only know year and month
    elif date_details == 1:
        return formats.date_format(
            dt, "MONTH_YEAR_DATE_FORMAT")
    # Date precision = we only know year
    elif date_details == 2:
        return formats.date_format(dt, "YEAR_DATE_FORMAT")


def floor_date(dt, date_details):
    """
    Only return meaningful and floored part of the date according to date_details
    """
    if not dt:
        return None

    # Date precision = full date
    if date_details == 0:
        return dt
    # Date precision = we only know year and month
    elif date_details == 1:
        return date(dt.year, dt.month, 1)
    # Date precision = we only know year
    elif date_details == 2:
        return date(dt.year, 1, 1)


def ceil_date(dt, date_details):
    """
    Only return meaningful and ceiled part of the date according to date_details
    """
    if not dt:
        return None

    # Date precision = full date
    if date_details == 0:
        return dt
    # Date precision = we only know year and month
    elif date_details == 1:
        return date(dt.year, dt.month, 1) + relativedelta.relativedelta(months=1, days=-1)
    # Date precision = we only know year
    elif date_details == 2:
        return date(dt.year, 12, 31)


def mangle_date(dt):
    """
    Return the date with month and day swapped when possible.

    Or original date otherwise
    Don't ask why
    """
    try:
        return date(dt.year, dt.day, dt.month)
    except (ValueError, AttributeError):
        return dt


def lookup_term(s):
    if s is None:
        return None

    return s.lower().strip(" *.,")


def blacklist(dct, fields):
    return {
        k: v for k, v in dct.items() if k not in fields
    }


def add_encrypted_url(dct, user, url):
    dct["url"] = settings.SITE_URL + reverse(
        url, args=[
            settings.SYMMETRIC_ENCRYPTOR.encrypt(
                b"%s|%s" % (user.pk, dct["id"]))
        ])

    return dct


def is_initial(s):
    return len(s) == 1 or s.endswith(".")


def unique(source):
    """
    Returns unique values from the list preserving order of initial list.
    :param source: An iterable.
    :type source: list
    :returns: List with unique values.
    :rtype: list
    """
    seen = set()
    return [seen.add(x) or x for x in source if x not in seen]


def parse_address(location):
    chunks = list(
        map(unicode.strip, location.split(u",")))

    zip_code = chunks[0].strip()
    orig = location
    city = ""
    street = ""
    appt = ""

    try:
        if len(chunks) == 3:
            city = u", ".join([chunks[2], chunks[1]])

        else:
            if u"обл" in chunks[1].lower() or u"крим" in chunks[1].lower():
                if u"район" in chunks[2].lower():
                    city = u", ".join([chunks[3], chunks[2], chunks[1]])

                    if len(chunks) > 4:
                        street = chunks[4]

                    if len(chunks) > 5:
                        appt = chunks[5]
                else:
                    city = u", ".join([chunks[2], chunks[1]])
                    if u"район" in chunks[3]:
                        street = chunks[4]

                        if len(chunks) > 5:
                            appt = chunks[5]
                    else:
                        street = chunks[3]

                        if len(chunks) > 4:
                            appt = chunks[4]
            else:
                city = chunks[1]
                street = chunks[3]
                if len(chunks) > 4:
                    appt = chunks[4]

        if not zip_code.isdigit():
            zip_code = ""

        # Sanity check
        if u"буд" in appt.lower() or appt == "" or appt.isdigit():
            return (zip_code, city, street, appt)
        else:
            logger.error(
                "Cannot parse %s, best results so far is %s" % (
                    location,
                    ", ".join([zip_code, city, street, appt])
                )
            )

            return None
    except IndexError:
        logger.error(
            "Cannot parse %s" % location
        )

        return None


def translate_into(chunk, lang="en"):
    curr_lang = get_language()
    activate(lang)
    res = unicode(ugettext_lazy(chunk or ""))
    activate(curr_lang)

    return res


# Cheesy implementation for now
def get_exchange_rate(curr, year):
    year = int(year)
    if year not in UAH_rates:
        year = 2018

    try:
        return UAH_rates[int(year)][curr.upper()]
    except KeyError:
        return 0.0


def localized_field(field_name, lang=settings.LANGUAGE_CODE):
    return "{}_{}".format(field_name, lang)


def get_localized_field(obj, field_name, lang=settings.LANGUAGE_CODE):
    return getattr(obj, localized_field(field_name, lang))


def localized_fields(field_names, langs=None):
    if langs is None:
        langs = [settings.LANGUAGE_CODE]

    return [localized_field(field, lang) for field in field_names for lang in langs]


def localized_field_map(field_name):
    mp = {}

    for lang in settings.LANGUAGE_CODES:
        mp[lang] = localized_field(field_name, lang)

    return mp
