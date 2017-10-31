# coding: utf-8
from __future__ import unicode_literals

from itertools import groupby

from django.utils.safestring import mark_safe
from django_markdown.utils import markdown as _markdown
from django_jinja import library
from jinja2.filters import _GroupTuple


@library.filter
def markdown(*args, **kwargs):
    return mark_safe('<div class="richtext">%s</div>' % _markdown(*args, **kwargs))


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
def groupbyandsort(value, attribute, reverse):
    attr = lambda x: getattr(x, attribute)

    grouped = [
        _GroupTuple(key, list(values)) for key, values
        in groupby(sorted(value, key=attr), attr)
    ]

    return sorted(grouped, key=lambda x: len(x.list), reverse=reverse)
