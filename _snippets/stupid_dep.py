import json
from core.models import Declaration, Company, Person2Company
from django.db.models import Q, Count
from django.conf import settings
from unicodecsv import DictWriter

if __name__ == "__main__":
    fp = open("/tmp/stupid_dep.csv", "w")
    w = DictWriter(
        fp,
        fieldnames=[
            "pep",
            "url",
            "photo",
        ],
        dialect="excel",
    )
    w.writeheader()

    for p2c in (
        Person2Company.objects.annotate(
            decls=Count(
                "from_person__declarations",
                filter=Q(from_person__declarations__confirmed="a"),
            )
        )
        .filter(Q(from_person__photo="") | Q(decls=0))
        .select_related("to_company", "from_person")
        .filter(to_company_id=63, date_finished__isnull=True)
    ):

        w.writerow({
            "pep": p2c.from_person.full_name,
            "url": settings.SITE_URL + p2c.from_person.get_absolute_url(),
            "photo": p2c.from_person.photo,
        })
