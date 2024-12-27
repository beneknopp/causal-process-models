from enum import Enum
from xml.etree.ElementTree import Element

from causal_model.CausalProcessStructure import AttributeActivities
from simulation_model.CPN import CPN


class Colset_Type(Enum):
    STANDARD = ""
    PRODUCT = "product"
    RECORD = "record"
    LIST = "list"
    WITH = "with"


class Standard_Colsets(Enum):
    STRING = "STRING"
    TIME = "TIME"
    REAL = "REAL"
    INT = "INT"
    BOOL = "BOOL"
    INTINF = "INTINF"
    UNIT = "UNIT"


class Colset(object):
    colset_id: str
    colset_name: str
    colset_type: Colset_Type
    timed: bool
    # for with-types
    rangemin: int;
    rangemax: int
    subcols: []

    def __init__(self, colset_id, colset_name, colset_type, subcols=[], timed=False):
        self.colset_id = colset_id
        self.colset_name = colset_name
        self.colset_type = colset_type
        self.subcols = subcols
        self.timed = timed

    def get_layout(self) -> str:
        return "colset " + self.colset_name + " = " \
               + self.__get_definition_string()

    def __get_definition_string(self) -> str:
        definition = ""
        if self.colset_type == Colset_Type.WITH:
            definition += self.subcols[0].colset_name + " with " + str(self.rangemin) + ".." + str(self.rangemax)
        if self.colset_type == Colset_Type.PRODUCT:
            definition += str(self.colset_type.value) + " "
            for subcol in self.subcols:
                definition += subcol.colset_name + "*"
            definition = definition[:-1]
        if self.colset_type == Colset_Type.LIST:
            definition += "list " + self.subcols[0].colset_name
        if self.colset_type == Colset_Type.STANDARD:
            definition += self.subcols[0].colset_name
        if self.timed:
            definition += " timed"
        definition += ";"
        return definition

    def set_colset_type(self, colset_type: Colset_Type):
        self.colset_type = colset_type

    def set_range(self, rangemin, rangemax):
        self.rangemin = rangemin
        self.rangemax = rangemax

    def set_subcols(self, subcols: []):
        self.subcols = subcols


class Colset_Map:
    colsets_by_id: dict
    colsets_by_name: dict
    many_colsets_names: set
    many_colset_by_single_colset: dict
    single_colset_by_many_colset: dict

    def __init__(self):
        self.colsets_by_id = dict()
        self.colsets_by_name = dict()
        self.many_colset_by_single_colset = dict()
        self.single_colset_by_many_colset = dict()
        self.many_colsets_names = set()

    def add(self, colset: Colset):
        colset_id = colset.colset_id
        colset_name = colset.colset_name
        if colset_id in self.colsets_by_id:
            raise ValueError("colset id already exists")
        if colset_name in self.colsets_by_name:
            raise ValueError("colset name already exists")
        self.colsets_by_id[colset_id] = colset
        self.colsets_by_name[colset_name] = colset

    def add_single_many_pair(self, single: Colset, many: Colset):
        self.many_colsets_names.add(many.colset_name)
        self.many_colset_by_single_colset[single] = many
        self.single_colset_by_many_colset[many] = single
        self.add(single)
        self.add(many)


class ColsetManager:
    colset_map: Colset_Map
    object_colsets: []
    event_colsets: []
    event_colsets_by_activity: dict
    additional_standard_colsets: []
    timed_id_colset: Colset

    COLSET_PREFIX = "C_"
    CASEID_COLSET_NAME = COLSET_PREFIX + "_case_id"

    def __init__(self, cpn: CPN):
        self.colset_map = Colset_Map()
        self.object_colsets = []
        self.event_colsets = []
        self.event_colsets_by_activity = dict()
        self.additional_standard_colsets = []
        self.cpn = cpn

    def parse_standard_colsets(self, declarations_block: Element):
        """
        this method reads the standard colsets (unit, bool, int etc.) from the template CPN
        and includes them in the class structures of the CPM-CPN-Converter.
        :param declarations_block:
        """
        color_elements = declarations_block.findall("color")
        for color_element in color_elements:
            colset_id = color_element.attrib["id"]
            colset_name = color_element.find("id").text
            colset = Colset(colset_id, colset_name, Colset_Type.STANDARD)
            self.__add_colset(colset)
        for standard_colset in Standard_Colsets:
            if not (standard_colset.value in self.colset_map.colsets_by_name.keys()):
                raise NameError("A declaration for the standard type '" + standard_colset.value + "' was not found.")
        # also might need those in complex colset declarations
        self.__add_primitive_colsets(["unit", "bool", "int", "intinf", "time", "real", "string"])

    def add_case_id_colset(self):
        """
        add an unambiguous colset to describe a token just with a case identifier
        """
        self.__add_alias_colset(Standard_Colsets.STRING, self.CASEID_COLSET_NAME)

    def get_case_id_colset(self):
        """
        get the unique case_id colset to describe a token just with a case identifier
        :return: the case_id colset
        """
        return self.colset_map.colsets_by_name[self.CASEID_COLSET_NAME]

    def add_activity_and_attribute_colsets(self,
                                           activity_ids: list[str],
                                           attribute_ids: list[str],
                                           attributes_with_last_observations: list[str],
                                           attributes_with_system_aggregations: list[str],
                                           attribute_activities: AttributeActivities
                                           ):
        """
        add standard colsets for activities and attributes of a causal model to be used in the CPN
        :param activity_ids:    the activities
        :param attribute_ids:   all attributes
        :param attributes_with_last_observations:   attributes for which simple dependencies exist so
        that last value observations of a case are needed
        :param attributes_with_system_aggregations:   attributes for which aggregated dependencies exist
        """
        for attr_id in attribute_ids:
            self.add_attribute_domain_colset(attr_id, "bool")
        for act_id in activity_ids:
            act_attribute_ids = [
                x.get_id() for x in
                attribute_activities.get_attributes_for_activity_id(act_id)]
            self.add_activity_colset(act_id, act_attribute_ids)
        for attr_id in attributes_with_last_observations:
            self.add_attribute_last_observation_colset(attr_id)
        for attr_id in attributes_with_system_aggregations:
            self.add_attribute_system_aggregation_colset(attr_id)

    def add_activity_colset(self, activity_id: str, attribute_ids: list[str]):
        activity_eaval_colset_name = self.get_activity_eaval_colset_name(activity_id)
        attribute_domain_colsets = [
            self.colset_map.colsets_by_name[self.get_attribute_domain_colset_name(attr_id)]
            for attr_id in attribute_ids
        ]
        self.__add_product_colset(activity_eaval_colset_name, attribute_domain_colsets)

    def get_named_entity_colset_prefix(self, entity_id):
        attribute_colset_prefix = self.COLSET_PREFIX + "_" + "_".join(entity_id.split(" "))
        return attribute_colset_prefix

    def get_activity_eaval_colset_name(self, act_id):
        activity_colset_prefix = self.get_named_entity_colset_prefix(act_id)
        activity_eaval_colset_name = activity_colset_prefix + "_eaval"
        return activity_eaval_colset_name

    def get_attribute_domain_colset_name(self, attr_id):
        attribute_colset_prefix = self.get_named_entity_colset_prefix(attr_id)
        attribute_domain_colset_name = attribute_colset_prefix + "_dom"
        return attribute_domain_colset_name

    def get_attribute_list_colset_name(self, attr_id):
        attribute_colset_prefix = self.get_named_entity_colset_prefix(attr_id)
        attribute_list_colset_name = attribute_colset_prefix + "_list"
        return attribute_list_colset_name

    def get_attribute_last_observation_colset_name(self, attr_id):
        attribute_colset_prefix = self.get_named_entity_colset_prefix(attr_id)
        attribute_last_observation_colset_name = attribute_colset_prefix + "_last"
        return attribute_last_observation_colset_name

    def get_attribute_system_aggregation_colset_name_single(self, attr_id):
        attribute_colset_prefix = self.get_named_entity_colset_prefix(attr_id)
        attribute_system_aggregation_colset_name = attribute_colset_prefix + "_single"
        return attribute_system_aggregation_colset_name

    def get_attribute_system_aggregation_colset_name_list(self, attr_id):
        attribute_colset_prefix = self.get_named_entity_colset_prefix(attr_id)
        attribute_system_aggregation_colset_name = attribute_colset_prefix + "_sys"
        return attribute_system_aggregation_colset_name

    def add_attribute_last_observation_colset(self, attribute_id: str):
        caseid_colset = self.get_case_id_colset()
        attribute_domain_colset = self.colset_map.colsets_by_name[self.get_attribute_domain_colset_name(attribute_id)]
        attribute_list_colset_name = self.get_attribute_list_colset_name(attribute_id)
        attribute_list_colset = self.__add_list_colset(attribute_list_colset_name, attribute_domain_colset)
        attribute_last_observation_colset_name = self.get_attribute_last_observation_colset_name(attribute_id)
        self.__add_product_colset(attribute_last_observation_colset_name, [
            caseid_colset, attribute_list_colset
        ])

    def add_attribute_system_aggregation_colset(self, attribute_id: str, activity_id: str):
        caseid_colset = self.get_case_id_colset()
        activity_eaval_colset = self.colset_map.colsets_by_name[self.get_activity_eaval_colset_name(activity_id)]
        attribute_domain_colset = self.colset_map.colsets_by_name[self.get_attribute_domain_colset_name(attribute_id)]
        attribute_system_aggregation_colset_name_single = self.get_attribute_system_aggregation_colset_name_single(
            attribute_id)
        attribute_system_aggregation_colset_name_list = self.get_attribute_system_aggregation_colset_name_list(
            attribute_id)
        system_aggregation_colset_single = self.__add_product_colset(
            attribute_system_aggregation_colset_name_single, [
                caseid_colset, activity_eaval_colset, attribute_domain_colset
        ])
        self.__add_list_colset(attribute_system_aggregation_colset_name_list, system_aggregation_colset_single)

    def add_attribute_domain_colset(self, attribute_id: str, domain_colset_name: str):
        alias = self.get_attribute_domain_colset_name(attribute_id)
        self.__add_alias_colset(domain_colset_name, alias)

    def __add_primitive_colsets(self, colset_names: []):
        for colset_name in colset_names:
            self.__add_standard_colset(colset_name)

    def __add_standard_colset(self, colset_name, colset_id=None):
        if colset_id is None:
            colset_id = self.cpn.give_ID()
        colset = Colset(colset_id, colset_name, colset_type=Colset_Type.STANDARD)
        self.__add_colset(colset)

    def __add_list_colset(self, colset_name, subcol):
        colset_id = self.cpn.give_ID()
        colset = Colset(colset_id, colset_name, colset_type=Colset_Type.LIST, subcols=[subcol])
        self.__add_colset(colset)
        return colset

    def __add_product_colset(self, colset_name, subcols):
        colset_id = self.cpn.give_ID()
        colset = Colset(colset_id, colset_name, Colset_Type.PRODUCT, subcols)
        self.__add_colset(colset)
        return colset

    def __add_colset(self, colset):
        self.colset_map.add(colset)

    def __add_alias_colset(self, colset_old_name, alias):
        colset_id = self.cpn.give_ID()
        colset_old: Colset = self.colset_map.colsets_by_name[colset_old_name]
        colset_new = Colset(colset_id, alias, colset_old.colset_type)
        self.__add_colset(colset_new)
        return colset_new
