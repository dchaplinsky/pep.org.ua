from elasticsearch_dsl import DocType, Completion, Index
from django.conf import settings
from core.utils import TranslatedField, blacklist
from cacheops import cached


class RangeRelevantEntitiesMixin(object):
    def relevant_related_persons(self):
        hl = getattr(self.meta, "highlight", None)

        if hl is not None:
            hl_uk = getattr(hl, "related_persons.person_uk", [])

            hl_en = getattr(hl, "related_persons.person_en", [])
        else:
            hl_en = []
            hl_uk = []

        highlighted = []
        peps = []
        rest = []

        for p in getattr(self, "related_persons", []):
            if p.person_uk in hl_uk:
                highlighted.append(p)
            elif p.person_en in hl_en:
                highlighted.append(p)
            elif p.is_pep:
                peps.append(p)
            else:
                rest.append(p)

        res = highlighted + peps + rest

        # Sorting the list so best matches will appear on top
        res.sort(
            key=lambda x: min(
                hl_en.index(x.person_en) if x.person_en in hl_en else 10000,
                hl_uk.index(x.person_uk) if x.person_uk in hl_uk else 10000,
            )
        )

        return res


person_idx = Index("pep_persons")
person_idx.settings(
    number_of_shards=settings.ES_NUMBER_OF_SHARDS,
    number_of_replicas=settings.ES_NUMBER_OF_REPLICAS,
)

@person_idx.doc_type
class Person(DocType, RangeRelevantEntitiesMixin):
    """Person document."""

    full_name_suggest = Completion(preserve_separators=False)

    translated_first_name = TranslatedField("first_name", "first_name_en")
    translated_last_name = TranslatedField("last_name", "last_name_en")
    translated_patronymic = TranslatedField("patronymic", "patronymic_en")

    translated_last_workplace = TranslatedField("last_workplace", "last_workplace_en")
    translated_last_job_title = TranslatedField("last_job_title", "last_job_title_en")

    @classmethod
    @cached(timeout=25 * 60 * 60)
    def get_all_persons(cls):
        return [
            blacklist(
                p.to_dict(),
                [
                    "full_name_suggest_en",
                    "dob_details",
                    "dob",
                    "full_name_suggest",
                    "last_job_id",
                    "risk_category",
                    "photo_path",
                    "terminated",
                    "last_modified",
                    "inn",
                    "inn_source",
                    "passport",
                    "passport_source",
                ],
            )
            for p in cls.search().scan()
        ]


company_idx = Index("pep_companies")
company_idx.settings(
    number_of_shards=settings.ES_NUMBER_OF_SHARDS,
    number_of_replicas=settings.ES_NUMBER_OF_REPLICAS,
)

@company_idx.doc_type
class Company(DocType, RangeRelevantEntitiesMixin):
    """Company document."""

    name_suggest = Completion(preserve_separators=False)

    translated_name = TranslatedField("name_uk", "name_en")

    @classmethod
    @cached(timeout=25 * 60 * 60)
    def get_all_companies(cls):
        return [
            blacklist(
                p.to_dict(),
                [
                    "code_chunks",
                    "name_suggest",
                    "name_suggest_output",
                    "name_suggest_output_en",
                    "last_modified",
                ],
            )
            for p in cls.search().scan()
        ]
