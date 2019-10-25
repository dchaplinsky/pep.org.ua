from neomodel import StructuredNode, StringProperty, BooleanProperty

class Person(StructuredNode):
    full_name = StringProperty()
    date_of_birth = StringProperty()
    type_of_official = StringProperty()
    is_pep = BooleanProperty()
    url_uk = StringProperty()
