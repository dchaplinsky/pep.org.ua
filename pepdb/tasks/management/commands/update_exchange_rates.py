# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import date

from django.core.management.base import BaseCommand
from django.utils.timezone import now
from django.conf import settings

from openexchangerates import OpenExchangeRatesClient
from tqdm import tqdm

from core.models import Declaration, ExchangeRate


class Command(BaseCommand):
    help = """
    Load exchange rates from openexchangerates
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "--retrieve_also_annual",
            help="Retrieve also annual rates",
            action="store_true",
            default=False,
        )

    def transform_rates(self, rates):
        uah_rate = rates["UAH"]

        return dict((curr, str(rate / uah_rate)) for curr, rate in rates.items())

    def handle(self, *args, **options):
        client = OpenExchangeRatesClient(settings.OPENEXCHANGERATES_KEY)
        dates = {now().date(): False}

        updated_recs = 0
        created_recs = 0

        if options["retrieve_also_annual"]:
            for year in list(
                Declaration.objects.exclude(year="")
                .values_list("year", flat=True)
                .distinct()
            ):
                year = int(year)
                if year < 1999:
                    continue

                dates[date(int(year), 12, 31)] = True

        for dt, annual in tqdm(dates.items()):
            rates = self.transform_rates(client.historical(dt)["rates"])
            _, created = ExchangeRate.objects.update_or_create(
                dt=dt, is_annual=annual, defaults={"rates": rates}
            )

            if created:
                created_recs += 1
            else:
                updated_recs += 1

        self.stdout.write(
            "{} records created, {} updated".format(created_recs, updated_recs)
        )
