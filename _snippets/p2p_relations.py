from core.models import Person2Person
from tqdm import tqdm
from unicodecsv import DictWriter

fp = open("/tmp/p2p.csv", "w")
w = DictWriter(fp, fieldnames=["person1", "person1_is", "person2", "person2_is", "proofs"])


qs = Person2Person.objects.select_related("from_person", "to_person").nocache()
w.writeheader()

for p2p in tqdm(qs.iterator(), total=qs.count()):
    w.writerow({
        "person1": p2p.from_person,
        "person2": p2p.to_person,
        "person1_is": p2p.get_from_relationship_type_display(),
        "person2_is": p2p.get_to_relationship_type_display(),
        "proofs": "\n".join([p.proof_title for p in p2p.proofs.all()])
    })