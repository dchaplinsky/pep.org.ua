# coding: utf-8
from __future__ import unicode_literals

from itertools import chain
from neo4j.types import Node, Relationship

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

from core.utils import TranslatedField


class BaseNode(StructuredNode):
    __abstract_node__ = True

    pk = IntegerProperty(unique_index=True)
    model = StringProperty()

    details_en = StringProperty()
    details_uk = StringProperty()
    details = TranslatedField("details_uk", "details_en")

    name_en = StringProperty()
    name_uk = StringProperty()
    name = TranslatedField("name_uk", "name_en")

    url_en = StringProperty()
    url_uk = StringProperty()
    url = TranslatedField("url_uk", "url_en")

    full_name = TranslatedField("full_name_uk", "full_name_en")
    full_name_en = StringProperty()
    full_name_uk = StringProperty()

    kind = TranslatedField("kind_uk", "kind_en")
    kind_en = StringProperty()
    kind_uk = StringProperty()

    description_en = StringProperty()
    description_uk = StringProperty()
    description = TranslatedField("description_uk", "description_en")

    def to_cytoscape(self):
        return {
            "pk": self.pk,
            "model": self.model,
            "details": self.details,
            "name": self.name,
            "url": self.url,
            "id": "{}-{}".format(self.model, self.pk),
            "full_name": self.full_name,
            "kind": self.kind,
            "description": self.description,
        }

    def inflate_all(self, response):
        nodes = set()
        rels = set()

        clss = {
            "person": Person,
            "company": Company,
            "country": Country,
            "person2person": Person2Person,
            "person2company": Person2Company,
            "person2country": Person2Country,
            "company2company": Company2Company,
            "company2country": Company2Country,
        }

        for p in response:
            for elem in chain.from_iterable(p):
                if isinstance(elem, Node):
                    nodes.add(elem)
                elif isinstance(elem, Relationship):
                    rels.add(elem)

        return (
            [
                clss[el["model"]].inflate(el)
                for el in (nodes)
                if "model" in el and el["model"] in clss
            ],
            [
                clss[el["model"]].inflate(el)
                for el in (rels)
                if "model" in el and el["model"] in clss
            ],
        )


class BaseRel(StructuredRel):
    pk = IntegerProperty()
    model = StringProperty()

    relationship_type_uk = StringProperty()
    reverse_relationship_type_uk = StringProperty()
    relationship_type_en = StringProperty()
    reverse_relationship_type_en = StringProperty()

    relationship_type = TranslatedField("relationship_type_uk", "relationship_type_en")
    reverse_relationship_type = TranslatedField(
        "reverse_relationship_type_uk", "reverse_relationship_type_en"
    )

    relationship_category = StringProperty()
    date_established_human = StringProperty()
    date_finished_human = StringProperty()
    date_confirmed_human = StringProperty()

    def to_cytoscape(self):
        return {
            "pk": self.pk,
            "model": self.model,
            "id": "{}-{}".format(self.model, self.pk),
            "relationship_category": self.relationship_category,
            "relation": self.relationship_type,
            "date_established_human": self.date_established_human,
            "date_finished_human": self.date_finished_human,
            "date_confirmed_human": self.date_confirmed_human,
            "source": self._source,
            "target": self._target,
            "is_latest": True,
        }

    @classmethod
    def inflate(cls, rel):
        srel = super(BaseRel, cls).inflate(rel)

        srel._source = "{}-{}".format(rel.start_node["model"], rel.start_node["pk"])
        srel._target = "{}-{}".format(rel.end_node["model"], rel.end_node["pk"])

        return srel


class Company2Company(BaseRel):
    equity_part = FloatProperty()

    def to_cytoscape(self):
        res = super(Company2Company, self).to_cytoscape()
        res.update(
            {
                "share": 0 if self.equity_part == -1 else self.equity_part,
            }
        )

        return res


class Person2Person(BaseRel):
    pass


class Person2Company(BaseRel):
    share = FloatProperty()
    is_employee = BooleanProperty()

    def to_cytoscape(self):
        res = super(Person2Company, self).to_cytoscape()
        res.update(
            {
                "share": 0 if self.share == -1 else self.share,
                "is_employee": self.is_employee,
            }
        )

        return res


class Person2Country(BaseRel):
    pass


class Company2Country(BaseRel):
    def to_cytoscape(self):
        res = super(Company2Country, self).to_cytoscape()
        res.update(
            {
                "source": "company-{}".format(self._start_node_id),
                "target": "country-{}".format(self._end_node_id),
            }
        )

        return res


# TODO: inheritance?
class Person(BaseNode):
    is_dead = BooleanProperty()
    is_pep = BooleanProperty()
    reason_of_termination = IntegerProperty()
    type_of_official = IntegerProperty()

    persons = RelationshipTo("Person", "Person2Person", model=Person2Person)
    companies = RelationshipTo("Company", "Person2Company", model=Person2Company)
    countries = RelationshipTo("Country", "Person2Country", model=Person2Country)

    def to_cytoscape(self):
        res = super(Person, self).to_cytoscape()
        res.update(
            {
                "is_dead": self.is_dead,
                "is_pep": self.is_pep,
                "type_of_official": self.type_of_official,
            }
        )

        return res


class Company(BaseNode):
    affiliated_with_pep = BooleanProperty()
    bank = BooleanProperty()
    is_closed = BooleanProperty()

    political_party = BooleanProperty()
    public_office = BooleanProperty()
    service_provider = BooleanProperty()
    state_company = BooleanProperty()
    state_enterprise = BooleanProperty()

    companies = RelationshipTo("Company", "Company2Company", model=Company2Company)
    persons = RelationshipFrom("Person", "Person2Company", model=Person2Company)
    countries = RelationshipTo("Country", "Company2Country", model=Company2Country)

    def to_cytoscape(self):
        res = super(Company, self).to_cytoscape()
        res.update(
            {
                "affiliated_with_pep": self.affiliated_with_pep,
                "bank": self.bank,
                "is_closed": self.is_closed,
                "political_party": self.political_party,
                "public_office": self.public_office,
                "service_provider": self.service_provider,
                "state_company": self.state_company,
                "state_enterprise": self.state_enterprise,
            }
        )

        return res

    def org_structure(self, q=None):
        # TODO: look into APOC path expanders
        # https://neo4j.com/docs/labs/apoc/3.4/graph-querying/path-expander/

        if q is None:
            # q = """
            #     MATCH path = (c)-[r:Company2Company*0..5 {relationship_category: "corporate_structure"}]-()<-[r2:Person2Company*1 {relationship_category: "owner"}]-(p:Person)
            #     WHERE id(c)={self}
            #     UNWIND NODES(path) AS n
            #         WITH path, SIZE(COLLECT(DISTINCT n)) AS path_nodes, COLLECT(DISTINCT n) as p_nodes
            #             WHERE path_nodes = LENGTH(path) + 1
            #             RETURN p_nodes, relationships(path)
            # """

            q = """
                MATCH path = (c)-[r:Company2Company*0..5 {relationship_category: "corporate_structure"}]-()<-[r2:Person2Company*1 {relationship_category: "owner"}]-(p:Person)
                WHERE id(c)={self}
                UNWIND NODES(path) AS n
                    WITH path, SIZE(COLLECT(DISTINCT n)) AS path_nodes, COLLECT(DISTINCT n) as p_nodes
                        WHERE path_nodes = LENGTH(path) + 1
                        unwind relationships(path) as p_rel
                        unwind p_nodes as p_node
                        with collect(distinct p_node) as uniq_nodes, collect(distinct p_rel) as uniq_rels
                        return uniq_nodes, uniq_rels
            """

        results, columns = self.cypher(q)
        return self.inflate_all(results)


class Country(BaseNode):
    is_jurisdiction = BooleanProperty()
    iso2 = StringProperty()
    iso3 = StringProperty()

    companies = RelationshipTo("Company", "Company2Country", model=Company2Country)
    persons = RelationshipFrom("Person", "Person2Country", model=Person2Country)

    def to_cytoscape(self):
        res = super(Company, self).to_cytoscape()
        res.update(
            {
                "is_jurisdiction": self.is_jurisdiction,
                "iso2": self.iso2,
                "iso3": self.iso3,
            }
        )

        return res


def neo4j_to_cytoscape(nodes, edges, root_node=None):
    res = {"edges": [], "nodes": []}

    for n in nodes:
        cyto = n.to_cytoscape()
        if n == root_node:
            cyto["is_main"] = True

        res["nodes"].append({"data": cyto})

    for e in edges:
        cyto = e.to_cytoscape()

        res["edges"].append({"data": cyto})

    return res
