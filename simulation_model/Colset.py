from enum import Enum
from xml.etree.ElementTree import Element

from causal_model.CausalProcessStructure import AttributeActivities
from simulation_model.cpn_utils.CPN import CPN
from simulation_model.cpn_utils.xml_utils.CPN_ID_Manager import CPN_ID_Manager


class Colset_Type(Enum):
    """
    A colset type is the data structure of a colset, that is,
    either STANDARD, PRODUCT, RECORD, LIST, or WITH.
    """
    STANDARD = ""
    PRODUCT = "product"
    RECORD = "record"
    LIST = "list"
    WITH = "with"


class Standard_Colsets(Enum):
    """
    A standard colset is a primitive data type, that is, STRING, TIME, REAL, INT,
    BOOL, INTINF, or UNIT.
    """
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
    rangemin: int
    rangemax: int
    subcols: []

    def __init__(self, colset_id, colset_name, colset_type: Colset_Type, subcols=None, timed=False):
        """
        A colset, that is, a (simple or complex data) type of tokens/places in a CPN.

        :param colset_id: the unique ID of the colset
        :param colset_name: the unique name of the colset
        :param colset_type: the Colset_Type of the colset
        :param subcols: for complex colsets, the sub-colsets.
        :param timed: whether the tokens shall be timed in the simulation model.
        """
        if subcols is None:
            subcols = []
        self.colset_id = colset_id
        self.colset_name = colset_name
        self.colset_type = colset_type
        self.subcols = subcols
        self.timed = timed

    def get_layout(self) -> str:
        """
        Get the string representation of the colset in the CPN XML.

        :return: the string representation
        """
        return "colset " + self.colset_name + " = " \
               + self.__get_definition_string()

    def __get_definition_string(self) -> str:
        """
        The inner definition string of the string representation in the CPN XML

        :return: the inner definition string
        """
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


class Colset_Map:
    colsets_by_id: dict
    colsets_by_name: dict
    ordered_colsets: list

    def __init__(self, cpn_id_manager: CPN_ID_Manager):
        """
        This class maintains the colsets of the simulation model and provides a map for them.
        """
        self.cpn_id_manager = cpn_id_manager
        self.colsets_by_id = dict()
        self.colsets_by_name = dict()
        self.ordered_colsets = list()

    def add(self, colset: Colset):
        """
        Add a colset.

        :param colset: the colset to be added
        :raises ValueError: if the ID or name of the colset to be added already exists

        """
        colset_id = colset.colset_id
        colset_name = colset.colset_name
        if colset_id in self.colsets_by_id:
            raise ValueError("colset id already exists")
        if colset_name in self.colsets_by_name:
            raise ValueError("colset name already exists")
        self.colsets_by_id[colset_id] = colset
        self.colsets_by_name[colset_name] = colset
        self.ordered_colsets.append(colset)

    def get_ordered_colsets(self):
        """
        Get all colsets for this simulation model. they are ordered and the order is assumed to be w.r.t.
        colset dependencies, so that the CPN interpreter will be happy.

        :return: all colsets for this simulation model
        """
        return self.ordered_colsets


class ColsetManager:

    colset_map: Colset_Map
    object_colsets: []
    event_colsets: []
    event_colsets_by_activity: dict
    additional_standard_colsets: []
    timed_id_colset: Colset
    parsed_colsets: set

    COLSET_PREFIX = "C_"
    CASEID_COLSET_NAME = COLSET_PREFIX + "cid"

    def __init__(self, cpn_id_manager: CPN_ID_Manager):
        """
        Create a new ColsetManager. This class makes takes care of the colsets of the CPN,
        for creating and querying them, and maintaining variables for them.
        """
        self.cpn_id_manager = cpn_id_manager
        self.colset_map = Colset_Map(cpn_id_manager)
        self.parsed_colsets = set()
        self.var_name_roots = list()
        self.colset_vars_map = dict()

    def parse_standard_colsets(self, declarations_block: Element):
        """
        This method reads the standard colsets (unit, bool, int etc.) from the template CPN
        and includes them in the class structures of the CPM-CPN-Converter.
        :param declarations_block: the XML element where the standard colsets are found
        """
        color_elements = declarations_block.findall("color")
        for color_element in color_elements:
            colset_id = color_element.attrib["id"]
            colset_name = color_element.find("id").text
            colset = Colset(colset_id, colset_name, Colset_Type.STANDARD)
            self.__add_colset(colset)
            self.parsed_colsets.add(colset)
        for standard_colset in Standard_Colsets:
            if not (standard_colset.value in self.colset_map.colsets_by_name.keys()):
                raise NameError("A declaration for the standard type '" + standard_colset.value + "' was not found.")

    def add_case_id_colset(self):
        """
        Add an unambiguous colset to describe a token just with a case identifier
        """
        self.__add_alias_colset(Standard_Colsets.STRING.value, self.CASEID_COLSET_NAME)

    def get_case_id_colset(self) -> Colset:
        """
        Get the unique case_id colset to describe a token just with a case identifier
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
        Add standard colsets for activities and attributes of a causal model to be used in the CPN
        :param activity_ids:    the activities
        :param attribute_ids:   all attributes
        :param attributes_with_last_observations:   attributes for which simple dependencies exist so
        that last value observations of a case are needed
        :param attributes_with_system_aggregations:   attributes for which aggregated dependencies exist
        """
        for attr_id in attribute_ids:
            self.add_attribute_domain_colset(attr_id, "BOOL")
        for act_id in activity_ids:
            act_attribute_ids = [
                x.get_id() for x in
                attribute_activities.get_attributes_for_activity_id(act_id)]
            self.add_activity_colset(act_id, act_attribute_ids)
        for attr_id in attributes_with_last_observations:
            self.add_attribute_last_observation_colset(attr_id)
        for attr_id in attributes_with_system_aggregations:
            act_id = attribute_activities.get_activity_for_attribute(attr_id)
            self.add_attribute_system_aggregation_colset(attr_id, act_id)

    def add_activity_colset(self, activity_id: str, attribute_ids: list[str]):
        """
        Add a colset that describes an event of that activity
        :param activity_id:  the id of the activity
        :param attribute_ids:  all attributes of that activity
        """
        activity_eaval_colset_name = self.get_activity_eaval_colset_name(activity_id)
        attribute_domain_colsets = [self.get_case_id_colset()]
        attribute_domain_colsets += [
            self.colset_map.colsets_by_name[self.get_attribute_domain_colset_name(attr_id)]
            for attr_id in attribute_ids
        ]
        self.__add_product_colset(activity_eaval_colset_name, attribute_domain_colsets)

    def get_named_entity_colset_prefix(self, entity_id):
        """
        Canonic prefix derivation for colsets to describe activities, attributes
        prefix can be extended to describe special types of colsets.

        :param entity_id: id of the activity or attribute
        :return: the prefix
        """
        attribute_colset_prefix = self.COLSET_PREFIX + "_".join(entity_id.split(" "))
        return attribute_colset_prefix

    def get_activity_eaval_colset_name(self, act_id):
        """
        Canonic naming scheme for event colsets.

        :param act_id: the id of the activity
        :return: the canonic name
        """
        activity_colset_prefix = self.get_named_entity_colset_prefix(act_id)
        activity_eaval_colset_name = activity_colset_prefix + "_EAVAL"
        return activity_eaval_colset_name

    def get_attribute_domain_colset_name(self, attr_id):
        """
        Canonic naming scheme for colsets that describe the domain (admissible values) of an attribute.

        :param attr_id: the id of the attribute
        :return: the canonic name
        """
        attribute_colset_prefix = self.get_named_entity_colset_prefix(attr_id)
        attribute_domain_colset_name = attribute_colset_prefix + "_DOMAIN"
        return attribute_domain_colset_name

    def get_attribute_list_colset_name(self, attr_id):
        """
        Canonic naming scheme for colsets that describe a list of admissible values of an attribute.

        :param attr_id: the id of the attribute
        :return: the canonic name
        """
        attribute_colset_prefix = self.get_named_entity_colset_prefix(attr_id)
        attribute_list_colset_name = attribute_colset_prefix + "_LIST"
        return attribute_list_colset_name

    def get_attribute_last_observation_colset_name(self, attr_id):
        """
        Canonic naming scheme for colsets that describes the last values
        of an attribute observed in the process.

        :param attr_id: the id of the attribute
        :return: the canonic name
        """
        attribute_colset_prefix = self.get_named_entity_colset_prefix(attr_id)
        attribute_last_observation_colset_name = attribute_colset_prefix + "_LAST"
        return attribute_last_observation_colset_name

    def get_attribute_system_aggregation_colset_name_single(self, attr_id):
        """
        Canonic naming scheme for colsets that describes ONE observed values
        of an attribute in the system (i.e., across cases).

        :param attr_id: the id of the attribute
        :return: the canonic name
        """
        attribute_colset_prefix = self.get_named_entity_colset_prefix(attr_id)
        attribute_system_aggregation_colset_name = attribute_colset_prefix + "_SINGLE"
        return attribute_system_aggregation_colset_name

    def get_attribute_system_aggregation_colset_name_list(self, attr_id):
        """
        Canonic naming scheme for colsets that describes ALL observed values
        of an attribute in the system (i.e., across cases).

        :param attr_id: the id of the attribute
        :return: the canonic name
        """
        attribute_colset_prefix = self.get_named_entity_colset_prefix(attr_id)
        attribute_system_aggregation_colset_name = attribute_colset_prefix + "_SYS"
        return attribute_system_aggregation_colset_name

    def add_attribute_last_observation_colset(self, attribute_id: str):
        """
        Create the colset to describe last observed value of an attribute.

        :param attribute_id: the id of the attribute
        :return: the colset
        """
        caseid_colset = self.get_case_id_colset()
        attribute_domain_colset = self.colset_map.colsets_by_name[self.get_attribute_domain_colset_name(attribute_id)]
        attribute_list_colset_name = self.get_attribute_list_colset_name(attribute_id)
        attribute_list_colset = self.__add_list_colset(attribute_list_colset_name, attribute_domain_colset)
        attribute_last_observation_colset_name = self.get_attribute_last_observation_colset_name(attribute_id)
        colset = self.__add_product_colset(attribute_last_observation_colset_name, [
            caseid_colset, attribute_list_colset
        ])
        return colset

    def add_attribute_system_aggregation_colset(self, attribute_id: str, activity_id: str):
        """
        Create the colset to describe all observed values of an attribute within the system.

        :param attribute_id: the id of the attribute
        :param activity_id: the activity of that attribute
        :return: the colset
        """
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
        colset = self.__add_list_colset(
            attribute_system_aggregation_colset_name_list, system_aggregation_colset_single)
        return colset

    def add_attribute_domain_colset(self, attribute_id: str, domain_colset_name: str):
        """
        Create the colset to describe the domain (admissible values) of an attribute.

        :param attribute_id: the id of the attribute
        :param domain_colset_name: the domain for which this colset is an alias (e.g., string, int)
        :return: the colset
        """
        alias = self.get_attribute_domain_colset_name(attribute_id)
        colset = self.__add_alias_colset(domain_colset_name, alias)
        return colset

    def __add_list_colset(self, colset_name, subcol):
        """
        Create a colset of list type.

        :param colset_name: the name of the new colset
        :param subcol: the colset to be embedded into a list structure
        :return: the list colset
        """
        colset_id = self.cpn_id_manager.give_ID()
        colset = Colset(colset_id, colset_name, colset_type=Colset_Type.LIST, subcols=[subcol])
        self.__add_colset(colset)
        return colset

    def __add_product_colset(self, colset_name, subcols):
        """
        Create a product colset for multiple colsets.

        :param colset_name: the name of the new product colset
        :param subcols: one or more colsets for which the product colset is to be created
        :return: the product colset
        """
        colset_id = self.cpn_id_manager.give_ID()
        colset = Colset(colset_id, colset_name, Colset_Type.PRODUCT, subcols)
        self.__add_colset(colset)
        return colset

    def __add_colset(self, colset):
        """
        Add a new colset to this object (ColsetManager) to be managed.

        :param colset: the colset to be added
        """
        self.colset_map.add(colset)

    def __add_alias_colset(self, colset_old_name, alias):
        """
        Create a colset that is an alias of a different colset.

        :param colset_old_name: the name for which the alias is to be created
        :param alias: the new name
        :return: the alias colset
        """
        colset_id = self.cpn_id_manager.give_ID()
        colset_old: Colset = self.colset_map.colsets_by_name[colset_old_name]
        colset_new = Colset(colset_id, alias, colset_old.colset_type, [colset_old])
        self.__add_colset(colset_new)
        return colset_new

    def get_ordered_colsets(self):
        """
        Get all colsets for this simulation model. They are ordered and the order is assumed to be w.r.t.
        colset dependencies, so that the CPN interpreter will be happy.

        :return: all colsets for this simulation model
        """
        return self.colset_map.get_ordered_colsets()

    def make_variables(self):
        """
        Make a variable for all colset that this ColsetManager is maintaining.
        """
        colset: Colset
        ordered_colsets = self.get_ordered_colsets()
        colset_names = [colset.colset_name for colset in ordered_colsets]
        for colset_name in colset_names:
            self.__make_variable_for_colset(colset_name)

    def __make_variable_for_colset(self, colset_name: str):
        """
        Make a variable for one colset that this ColsetManager is maintaining.

        :param colset_name: the name of the colset for which variables are to be created
        """
        lower_name = colset_name.lower()
        var_name = lower_name[:]
        if var_name.startswith("c_"):
            var_name = var_name[2:]
        if colset_name not in self.colset_vars_map:
            self.colset_vars_map[colset_name] = set()
        vars_count = len(self.colset_vars_map[colset_name]) + 1
        var_name = "v_" + var_name + "_" + str(vars_count)
        self.colset_vars_map[colset_name].add(var_name)
        self.var_name_roots = list(set(self.var_name_roots + [lower_name]))

    def get_one_var(self, colset_name) -> str:
        """
        Get one variable for a colset.

        :param colset_name: the name of the colset
        :return: a variable
        """
        colset_vars = list(set(self.colset_vars_map[colset_name]))
        colset_vars.sort()
        return colset_vars[0]

    def get_some_vars(self, colset_name, number) -> list[str]:
        """
        Get multiple variables for a colset.

        :param colset_name: the name of the colset
        :param number: the number of variables to be retrieved
        :return: the variables
        """
        colset_vars = self.colset_vars_map[colset_name][:]
        n = len(colset_vars)
        if n < number:
            for i in range(number - n):
                self.__make_variable_for_colset(colset_name)
        colset_vars = self.colset_vars_map[colset_name]
        return colset_vars[:number]
