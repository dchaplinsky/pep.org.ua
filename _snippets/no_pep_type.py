from core.models import Person
from tqdm import tqdm
from unicodecsv import writer
from django.conf import settings

if __name__ == "__main__":
    q = Person.objects.filter(type_of_official__isnull=True)

    with open("/tmp/no_pep_type.csv", "w") as fp:
        w = writer(fp)

        for p in tqdm(
            q.nocache().iterator(),
            total=q.count()
        ):
            w.writerow([p.full_name, settings.SITE_URL + p.get_absolute_url()])
