from django.conf import settings
from django.db.models import Count, F

from core.forms import FeedbackForm
from core.models import Country


def feedback_processor(request):
    return {"feedback_form": FeedbackForm()}


def config_processor(request):
    return {
        "SITE_URL": settings.SITE_URL,
        "SITEHEART_ID": settings.SITEHEART_ID,
        "GA_ID": settings.GA_ID,
    }


def default_country(request):
    used_countries = (
        Country.objects.annotate(
            persons_count=Count("person2country", distinct=True),
            companies_count=Count("company2country", distinct=True),
        )
        .annotate(usages=F("persons_count") + F("companies_count"))
        .exclude(usages=0)
        .exclude(iso2="")
        .order_by("-usages")
    )

    return {
        "default_country": Country.objects.get(iso3=settings.DEFAULT_COUNTRY_ISO3),
        "used_countries": used_countries,
    }
