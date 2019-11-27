from django.core.urlresolvers import reverse
from django.utils.translation import activate
from django.db.models import Count, F
from django.conf import settings

from qartez.sitemaps import RelAlternateHreflangSitemap

from cms_pages.models import StaticPage
from core.models import Person, Company, Country


class MainXML(RelAlternateHreflangSitemap):
    protocol = "https"

    def items(self):
        pages = [
            ('wagtail_serve', ['']),
            ('feedback', []),
            ('countries_home', []),
        ]
        return pages

    def location(self, item):
        return reverse(item[0], args=item[1])

    def alternate_hreflangs(self, obj):
        res = []

        for lang, _ in settings.LANGUAGES:
            activate(lang)
            res.append(
                (lang, "%s%s" % (settings.SITE_URL, self.location(obj)))
            )

        return res


class CountriesXML(RelAlternateHreflangSitemap):
    protocol = "https"

    def items(self):
        return Country.objects.annotate(
            persons_count=Count("person2country"),
            companies_count=Count("company2country")).annotate(
            usages=F("persons_count") + F("companies_count")).exclude(
            usages=0, iso2="").order_by("-usages")

    def location(self, item):
        activate(settings.LANGUAGE_CODE)
        return reverse("countries", args=[item.iso2])

    def alternate_hreflangs(self, obj):
        res = []

        for lang, _ in settings.LANGUAGES:
            activate(lang)
            res.append(
                (lang, "%s%s" % (settings.SITE_URL, self.location(obj)))
            )

        return res


class PersonXML(RelAlternateHreflangSitemap):
    protocol = "https"

    def items(self):
        return Person.objects.all()

    def location(self, item):
        activate(settings.LANGUAGE_CODE)
        return item.get_absolute_url()

    def alternate_hreflangs(self, obj):
        return [
            (lang, "%s%s" % (settings.SITE_URL, obj.localized_url(lang)))
            for lang, _ in settings.LANGUAGES]


class CompanyXML(RelAlternateHreflangSitemap):
    protocol = "https"

    def items(self):
        return Company.objects.all()

    def location(self, item):
        activate(settings.LANGUAGE_CODE)
        return item.get_absolute_url()

    def alternate_hreflangs(self, obj):
        return [
            (lang, "%s%s" % (settings.SITE_URL, obj.localized_url(lang)))
            for lang, _ in settings.LANGUAGES]


class StaticXML(RelAlternateHreflangSitemap):
    protocol = "https"

    def items(self):
        return list(StaticPage.objects.live())

    def location(self, item):
        return item.url

    def alternate_hreflangs(self, obj):
        return [
            (lang, "%s%s" % (settings.SITE_URL, obj.localized_url(lang)))
            for lang, _ in settings.LANGUAGES]
