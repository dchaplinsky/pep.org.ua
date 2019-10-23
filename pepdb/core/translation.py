from modeltranslation.translator import translator, TranslationOptions
from core.models import (
    Country, Document, Person, Company, Person2Company, Declaration,
    Person2Person, RelationshipProof, DeclarationToLink, DeclarationToWatch,
    CompanyCategories, Rule)


class CountryTranslationOptions(TranslationOptions):
    fields = ("name",)


class DocumentTranslationOptions(TranslationOptions):
    fields = ("name",)


class PersonTranslationOptions(TranslationOptions):
    fields = ("last_name", "first_name", "patronymic", "wiki", "city_of_birth",
              "reputation_assets", "reputation_sanctions", "reputation_crimes",
              "reputation_manhunt", "reputation_convictions",
              "title", "description", "also_known_as", "wiki_url")


class CompanyTranslationOptions(TranslationOptions):
    fields = ("name", "short_name", "city", "street", "appt", "wiki",
              "other_founders", "other_recipient", "other_owners",
              "other_managers", "bank_name", "sanctions")


class Person2PersonTranslationOptions(TranslationOptions):
    fields = ("relationship_details",)


class Person2CompanyTranslationOptions(TranslationOptions):
    fields = ("relationship_type",)


class RelationshipProofTranslationOptions(TranslationOptions):
    fields = ('proof_title', )


class DeclarationTranslationOptions(TranslationOptions):
    fields = ("position", "office", "region",)


class RuleTranslationOptions(TranslationOptions):
    fields = ("template",)


translator.register(Country, CountryTranslationOptions)
translator.register(Document, DocumentTranslationOptions)
translator.register(Person, PersonTranslationOptions)
translator.register(Company, CompanyTranslationOptions)
translator.register(CompanyCategories, CompanyTranslationOptions)
translator.register(Person2Company, Person2CompanyTranslationOptions)
translator.register(Declaration, DeclarationTranslationOptions)
translator.register(DeclarationToLink, DeclarationTranslationOptions)
translator.register(DeclarationToWatch, DeclarationTranslationOptions)
translator.register(Person2Person, Person2PersonTranslationOptions)
translator.register(RelationshipProof, RelationshipProofTranslationOptions)
translator.register(Rule, RuleTranslationOptions)
