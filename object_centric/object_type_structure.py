from enum import Enum

from utils.validators import validate_condition

DEFAULT_OBJECT_TYPE_NAME = "CASE"


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
        self.__object_type_name = object_type_name
        if object_type_id is None:
            object_type_id = "_".join(object_type_name.split(" "))
        self.__object_type_id = object_type_id

    def get_name(self):
        return self.__object_type_name

    def get_id(self):
        return self.__object_type_id


DEFAULT_OBJECT_TYPE = ObjectType(DEFAULT_OBJECT_TYPE_NAME)


def get_default_object_type_name():
    return DEFAULT_OBJECT_TYPE_NAME


def get_default_object_type():
    return DEFAULT_OBJECT_TYPE


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
        rs = self.get_object_type_relations()
        ots = self.get_object_types()
        key_pairs = [(r.get_ot1(), r.get_ot2()) for r in rs]
        validate_condition(len(set(key_pairs)) == len(self.get_object_type_relations()))
        validate_condition(all(k1 != k2 for (k1, k2) in key_pairs))
        validate_condition(all(k1 in ots and k2 in ots for (k1, k2) in key_pairs))

    def __init__(self, object_types: list[ObjectType]=None, object_type_relations: list[ObjectTypeRelation]=None):
        if object_types is None:
            if object_type_relations is not None:
                raise ValueError()
            object_types = [get_default_object_type()]
            object_type_relations = []
        self.__object_types = object_types
        self.__object_type_relations = object_type_relations
        self.__validate()

    def get_object_types(self):
        return self.__object_types

    def get_object_type_relations(self):
        return self.__object_type_relations

    def get_sorted_relations(self, ot: ObjectType) -> list[Multiplicity, ObjectType]:
        sorted_relations = []
        for r in self.get_object_type_relations():
            if r.get_ot1() is ot:
                sorted_relations.append((r.get_m2(), r.get_ot2()))
            if r.get_ot2() is ot:
                sorted_relations.append((r.get_m1(), r.get_ot1()))
        return sorted_relations

    def has_multiplicity(self, ot_tuple: tuple[ObjectType, ObjectType], m: Multiplicity):
        ot1, ot2 = ot_tuple
        return any(
            (ot1 is r.get_ot1() and ot2 is r.get_ot2() and r.get_m2() is m) or
            (ot2 is r.get_ot1() and ot1 is r.get_ot2() and r.get_m1() is m)
            for r in self.__object_type_relations)

    def get_to_1_relations_for_object_type(self, object_type):
        rs = self.get_object_type_relations()
        r: ObjectTypeRelation
        rs1 = list(filter(lambda r: r.get_ot1() is object_type and r.get_m2() is Multiplicity.ONE, rs))
        rs1 = list(map(lambda r: r.get_ot2(), rs1))
        rs2 = list(filter(lambda r: r.get_ot2() is object_type and r.get_m1() is Multiplicity.ONE, rs))
        rs2 = list(map(lambda r: r.get_ot1(), rs2))
        return rs1 + rs2

    def get_to_N_relations_for_object_type(self, object_type):
        rs = self.get_object_type_relations()
        r: ObjectTypeRelation
        rs1 = list(filter(lambda r: r.get_ot1() is object_type and r.get_m2() is Multiplicity.MANY, rs))
        rs1 = list(map(lambda r: r.get_ot2(), rs1))
        rs2 = list(filter(lambda r: r.get_ot2() is object_type and r.get_m1() is Multiplicity.MANY, rs))
        rs2 = list(map(lambda r: r.get_ot1(), rs2))
        return rs1 + rs2