# coding: utf-8
from __future__ import unicode_literals

from itertools import groupby
from urlparse import urlsplit, urlunsplit
from urllib import unquote_plus
from decimal import Decimal, InvalidOperation

from django.utils.safestring import mark_safe
from django_markdown.utils import markdown as _markdown
from django.core.urlresolvers import reverse, resolve, Resolver404, NoReverseMatch
from django.utils.translation import override, get_language
from django.conf import settings

from core.utils import get_localized_field, get_exchange_rate
from django_jinja import library
from jinja2.filters import _GroupTuple



@library.filter
def markdown(*args, **kwargs):
    return mark_safe('<div class="richtext">%s</div>' % _markdown(*args, **kwargs))


@library.filter
def rule_val(value):
    return mark_safe('<strong>%s</strong>' % value)

@library.filter
def rule_money(value):
    return mark_safe('<strong>%s</strong>' % curformat(value))


@library.global_function
def updated_querystring(request, params):
    """Updates current querystring with a given dict of params, removing
    existing occurrences of such params. Returns a urlencoded querystring."""
    original_params = request.GET.copy()
    for key in params:
        if key in original_params:
            original_params.pop(key)
    original_params.update(params)
    return original_params.urlencode()


@library.filter
def curformat(value):
    if not isinstance(value, basestring):
        value = unicode(value)

    if value and value != "0" and value != "0.0":
        currency = ""
        if "$" in value:
            value = value.replace("$", "")
            currency = "USD "

        if "£" in value:
            value = value.replace("£", "")
            currency = "GBP "

        if "€" in value or "Є" in value:
            value = value.replace("€", "").replace("Є", "")
            currency = "EUR "

        try:
            return '{}{:,.2f}'.format(
                currency,
                float(value.replace(',', '.'))).replace(
                    ',', ' ').replace('.', ',')
        except ValueError:
            return value
    else:
        return mark_safe('<i class="i-value-empty">—</i>')


@library.filter
def spaceformat(value):
    try:
        return '{:,.2f}'.format(
            float(value.replace(',', '.'))).rstrip("0").rstrip(".")
    except ValueError:
        if value.startswith("."):
            return "0" + value
        else:
            return value


@library.filter
def groupbyandsort(value, attribute, sort_attribute, reverse):
    attr = lambda x: getattr(x, attribute)

    grouped = [
        _GroupTuple(key, list(values)) for key, values
        in groupby(sorted(value, key=attr), attr)
    ]

    return sorted(grouped, key=lambda x: getattr(x.list[0], sort_attribute), reverse=reverse)


@library.filter
def is_list(value):
    return isinstance(value, list)

@library.filter
def xmlize(value):
    if isinstance(value, bool):
        return int(value)
    else:
        return value

def smart_unquote_plus(v):
    if isinstance(v, basestring):
        return unquote_plus(v)
    if isinstance(v, tuple):
        return tuple(unquote_plus(m) for m in v)
    if isinstance(v, list):
        return [unquote_plus(m) for m in v]

    return v


def orig_translate_url(url, lang_code, orig_lang_code=None):
    """
    Given a URL (absolute or relative), try to get its translated version in
    the `lang_code` language (either by i18n_patterns or by translated regex).
    Return the original URL if no translated version is found.
    """
    parsed = urlsplit(url)
    try:
        if orig_lang_code is None:
            match = resolve(parsed.path)
        else:
            with override(orig_lang_code):
                match = resolve(parsed.path)   
    except Resolver404:
        pass
    else:
        to_be_reversed = "%s:%s" % (match.namespace, match.url_name) if match.namespace else match.url_name
        with override(lang_code):
            try:
                match.kwargs = {k: smart_unquote_plus(v) for k, v in match.kwargs.items()}
                match.args = [smart_unquote_plus(v) for v in match.args]
                url = reverse(to_be_reversed, args=match.args, kwargs=match.kwargs)
            except NoReverseMatch:
                pass
            else:
                url = urlunsplit(("https", parsed.netloc, url, parsed.query, parsed.fragment))

    return url


@library.global_function
def translate_url(request, language):
    if isinstance(request, str):
        url = request
    else:
        url = request.build_absolute_uri()
    return orig_translate_url(url, language)


@library.filter
def translated(value, field, fallback=True):
    lang = get_language()
    val = get_localized_field(value, field, lang)
    if val or not fallback:
        return val
    else:
        return get_localized_field(value, field, settings.LANGUAGE_CODE)

@library.filter
def convert_curr(value, year):
    lang = get_language()

    if lang == "en" and value:
        try:
            value = Decimal(str(value).replace(" ", "").replace(",", ".")) / get_exchange_rate("USD", year)
        except (TypeError, ZeroDivisionError, InvalidOperation):
            pass

    return value
