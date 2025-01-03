from enum import Enum

from utils.validators import validate_condition


class Multiplicity(Enum):
    """
    These are the possible multiplicities of relations between two object types:
    ONE if there is always one, ANY if there can be any number, MANY if there is at least one.

    """
    ONE = "ONE",  # 1
    ANY = "ANY"  # 0..*
    MANY = "MANY"  # 1..*


class ObjectType:

    def __init__(self, object_type_name: str, object_type_id: str = None):
        self.object_type_name = object_type_name
        if object_type_id is None:
            object_type_id = "_".join(object_type_name.split(" "))
        self.object_type_id = object_type_id


class ObjectTypeRelation:

    def __init__(self, ot1: ObjectType, m1: Multiplicity, m2: Multiplicity, ot2: ObjectType):
        """
        This class describes the multiplicities of relations between two object types in a object type structure.
        The order of the constructor parameters corresponds to the logic of a UML class diagram:
        ot1,m1,m2,ot2 means that each ot1 object has m2 objects of type ot2,
        and each ot2 object has m1 objects of type ot1.

        :param ot1: The first object type
        :param m1: The number of first-type objects at second-type objects
        :param m2: The number of second-type objects at first-type objects
        :param ot2: The second object type
        """
        self.__ot1 = ot1
        self.__m1 = m1
        self.__m2 = m2
        self.__ot2 = ot2

    def get_ot1(self):
        return self.__ot1

    def get_ot2(self):
        return self.__ot2

    def get_m1(self):
        return self.__m1

    def get_m2(self):
        return self.__m2


class ObjectTypeStructure:

    def __validate(self):
        r: ObjectTypeRelation
        key_pairs = [(r.get_ot1(), r.get_ot2()) for r in self.object_type_relations]
        validate_condition(len(set(key_pairs)) == len(self.object_type_relations))
        validate_condition(all(k1 != k2 for (k1, k2) in key_pairs))

    def __init__(self, object_types: list[ObjectType], object_type_relations: list[ObjectTypeRelation]):
        self.object_types = object_types
        self.object_type_relations = object_type_relations
        self.__validate()
