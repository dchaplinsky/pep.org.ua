from core.models import Person2Company, Company2Company
from unicodecsv import DictWriter
from django.utils.translation import activate
from django.conf import settings
from collections import Counter
from tqdm import tqdm

activate(settings.LANGUAGE_CODE)

with open("/tmp/positions.csv", "w") as fp:
    w = DictWriter(fp, fieldnames=["person", "relation", "company", "url"])

    w.writeheader()

    for p2c in tqdm(
        Person2Company.objects.all()
        .select_related("from_person", "to_company")
        .nocache()
        .iterator()
    ):
        w.writerow(
            {
                "person": p2c.from_person.full_name,
                "relation": p2c.relationship_type,
                "company": p2c.to_company.name,
                "url": "https://pep.org.ua{}".format(
                    p2c.from_person.get_absolute_url()
                ),
            }
        )


with open("/tmp/relations.csv", "w") as fp:
    w = DictWriter(fp, fieldnames=["company1", "relation", "back_relation", "company2", "url"])

    w.writeheader()

    for c2c in tqdm(
        Company2Company.objects.all()
        .select_related("from_company", "to_company")
        .nocache()
        .iterator()
    ):
        w.writerow(
            {
                "company1": c2c.from_company.name,
                "relation": c2c.relationship_type,
                "back_relation": c2c.reverse_relationship_type,
                "company2": c2c.to_company.name,
                "url": "https://pep.org.ua{}".format(
                    c2c.from_company.get_absolute_url()
                ),
            }
        )


with open("/tmp/relations_cnt.csv", "w") as fp:
    w = DictWriter(fp, fieldnames=["relation", "back_relation", "count"])

    w.writeheader()

    cnt = Counter()

    for c2c in tqdm(
        Company2Company.objects.all()
        .nocache()
        .iterator()
    ):
        cnt.update([(c2c.relationship_type, c2c.reverse_relationship_type)])


    for k, v in cnt.most_common():
        w.writerow(
            {
                "relation": k[0],
                "back_relation": k[1],
                "count": v,
            }
        )
