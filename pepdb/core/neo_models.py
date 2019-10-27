from neomodel import (
    StructuredNode,
    StringProperty,
    BooleanProperty,
    IntegerProperty,
    FloatProperty,
    StructuredRel,
    RelationshipTo,
    RelationshipFrom,
)

class BaseRel(StructuredRel):
    relationship_type_uk = StringProperty()
    reverse_relationship_type_uk = StringProperty()
    relationship_type_en = StringProperty()
    reverse_relationship_type_en = StringProperty()

    relationship_category = StringProperty()
    date_established_human = StringProperty()
    date_finished_human = StringProperty()
    date_confirmed_human = StringProperty()


class Company2Company(BaseRel):
    equity_part = FloatProperty()


class Person2Person(BaseRel):
    pass

class Person2Company(BaseRel):
    share = FloatProperty()
    is_employee = BooleanProperty()

class Person2Country(BaseRel):
    pass


class Company2Country(BaseRel):
    pass


# TODO: inheritance?
class Person(StructuredNode):
    description_en = StringProperty()
    description_uk = StringProperty()
    details_en = StringProperty()
    details_uk = StringProperty()
    full_name_en = StringProperty()
    full_name_uk = StringProperty()
    is_dead = BooleanProperty()
    is_pep = BooleanProperty()
    kind = StringProperty()
    kind_en = StringProperty()
    kind_uk = StringProperty()
    model = StringProperty()
    name_en = StringProperty()
    name_uk = StringProperty()
    pk = IntegerProperty(unique_index=True)
    reason_of_termination = IntegerProperty()
    type_of_official = IntegerProperty()
    url = StringProperty()
    url_en = StringProperty()
    url_uk = StringProperty()

    persons = RelationshipTo("Person", "Person2Person", model=Person2Person)
    companies = RelationshipTo("Company", "Person2Company", model=Person2Company)
    countries = RelationshipTo("Country", "Person2Country", model=Person2Country)


class Company(StructuredNode):
    affiliated_with_pep = BooleanProperty()
    bank = BooleanProperty()
    details_en = StringProperty()
    details_uk = StringProperty()
    full_name_en = StringProperty()
    full_name_uk = StringProperty()
    is_closed = BooleanProperty()
    kind_en = StringProperty()
    kind_uk = StringProperty()
    model = StringProperty()
    name_en = StringProperty()
    name_uk = StringProperty()
    pk = IntegerProperty(unique_index=True)
    political_party = BooleanProperty()
    public_office = BooleanProperty()
    service_provider = BooleanProperty()
    state_company = BooleanProperty()
    state_enterprise = BooleanProperty()
    url_en = StringProperty()
    url_uk = StringProperty()

    companies = RelationshipTo("Company", "Company2Company", model=Company2Company)
    persons = RelationshipFrom("Person", "Person2Company", model=Person2Company)
    countries = RelationshipTo("Country", "Company2Country", model=Company2Country)


class Country(StructuredNode):
    details_en = StringProperty()
    details_uk = StringProperty()
    is_jurisdiction = BooleanProperty()
    iso2 = StringProperty()
    iso3 = StringProperty()
    model = StringProperty()
    name_en = StringProperty()
    name_uk = StringProperty()
    pk = IntegerProperty(unique_index=True)
    url_en = StringProperty()
    url_uk = StringProperty()

    companies = RelationshipTo("Company", "Company2Country", model=Company2Country)
    persons = RelationshipFrom("Person", "Person2Country", model=Person2Country)
