from enum import Enum
from xml.etree.ElementTree import Element

from causal_model.causal_process_structure import AttributeActivities, CPM_Attribute, CPM_Attribute_Domain_Type, \
    CPM_Activity, CPM_Domain, CPM_Categorical_Domain
from object_centric.object_type_structure import ObjectType, ObjectTypeStructure, Multiplicity
from simulation_model.cpn_utils.xml_utils.cpn_id_managment import CPN_ID_Manager


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
            self: WithColset
            definition += "with " + " | ".join(self.labels)
        if self.colset_type == Colset_Type.PRODUCT:
            definition += "product "
            definition += "*".join(subcol.colset_name for subcol in self.subcols)
        if self.colset_type == Colset_Type.LIST:
            definition += "list " + self.subcols[0].colset_name
        if self.colset_type == Colset_Type.STANDARD:
            definition += self.subcols[0].colset_name
        if self.colset_type == Colset_Type.RECORD:
            definition += "record "
            definition += " * ".join(subcol.colset_name.lower() + " : " + subcol.colset_name for subcol in self.subcols)
        if self.timed:
            definition += " timed"
        definition += ";"
        return definition


class WithColset(Colset):

    def __init__(self, colset_id, colset_name, labels, timed=False):
        super().__init__(colset_id, colset_name, Colset_Type.WITH, subcols=[], timed=timed)
        self.labels = labels


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


COLSET_PREFIX = "C_"
EVENTID_COLSET_NAME = COLSET_PREFIX + "eid"
TIMEDINT_COLSET_NAME = COLSET_PREFIX + "timedint"


def get_timed_int_colset_name():
    return TIMEDINT_COLSET_NAME


def get_object_type_ID_colset_name(ot: ObjectType):
    return COLSET_PREFIX + ot.get_id() + "ID"


def get_object_type_ID_list_colset_name(ot: ObjectType):
    return COLSET_PREFIX + ot.get_id() + "ID_LIST"


def get_object_type_colset_name(ot: ObjectType):
    return COLSET_PREFIX + ot.get_id()


def get_object_type_list_colset_name(ot: ObjectType):
    return COLSET_PREFIX + ot.get_id() + "_LIST"


def get_domain_colset_name(domain: CPM_Domain):
    return COLSET_PREFIX + domain.get_id()


def get_activity_timestamps_colset_name(act: CPM_Activity):
    return COLSET_PREFIX + "_" + act.get_id() + "_TIMES"


def get_named_entity_colset_prefix(entity_id):
    """
    Canonic prefix derivation for colsets to describe activities, attributes
    prefix can be extended to describe special types of colsets.

    :param entity_id: id of the activity or attribute
    :return: the prefix
    """
    attribute_colset_prefix = COLSET_PREFIX + "_".join(entity_id.split(" "))
    return attribute_colset_prefix


def get_real_colset_name():
    """
    Get the unique name for the real colset
    """
    return Standard_Colsets.REAL.value


def get_attribute_all_observations_colset_name(attribute_id) -> str:
    attribute_colset_prefix = get_named_entity_colset_prefix(attribute_id)
    attribute_all_observations_colset_name = attribute_colset_prefix + "_ALL"
    return attribute_all_observations_colset_name


def get_attribute_observations_list_colset_name(attribute_id: str) -> str:
    attribute_colset_prefix = get_named_entity_colset_prefix(attribute_id)
    attribute_all_observations_colset_name = attribute_colset_prefix + "_OBS_LIST"
    return attribute_all_observations_colset_name


def get_attribute_context_observation_colset_name(attribute_id) -> str:
    attribute_colset_prefix = get_named_entity_colset_prefix(attribute_id)
    attribute_last_observation_colset_name = attribute_colset_prefix + "_CONTEXT"
    return attribute_last_observation_colset_name


def get_attribute_system_aggregation_colset_name_single(attribute_id):
    """
    Canonic naming scheme for colsets that describes ONE observed values
    of an attribute in the system (i.e., across cases).

    :param attribute_id: the id of the attribute
    :return: the canonic name
    """
    attribute_colset_prefix = get_named_entity_colset_prefix(attribute_id)
    attribute_system_aggregation_colset_name = attribute_colset_prefix + "_SINGLE"
    return attribute_system_aggregation_colset_name


def get_attribute_system_aggregation_colset_name_list(attribute_id):
    """
    Canonic naming scheme for colsets that describes ALL observed values
    of an attribute in the system (i.e., across cases).

    :param attribute_id: the id of the attribute
    :return: the canonic name
    """
    attribute_colset_prefix = get_named_entity_colset_prefix(attribute_id)
    attribute_system_aggregation_colset_name = attribute_colset_prefix + "_SYS"
    return attribute_system_aggregation_colset_name


def get_attribute_domain_colset_name(attribute_id):
    """
    Canonic naming scheme for colsets that describe the domain (admissible values) of an attribute.

    :param attribute_id: the id of the attribute
    :return: the canonic name
    """
    attribute_colset_prefix = get_named_entity_colset_prefix(attribute_id)
    attribute_domain_colset_name = attribute_colset_prefix + "_DOM"
    return attribute_domain_colset_name


def get_attribute_list_colset_name(attribute_id):
    """
    Canonic naming scheme for colsets that describe a list of admissible values of an attribute.

    :param attribute_id: the id of the attribute
    :return: the canonic name
    """
    attribute_colset_prefix = get_named_entity_colset_prefix(attribute_id)
    attribute_list_colset_name = attribute_colset_prefix + "_LIST"
    return attribute_list_colset_name


def get_attribute_last_observation_colset_name(attribute_id) -> str:
    """
    Canonic naming scheme for colsets that describes the last values
    of an attribute observed in the process.

    :param attribute_id: the id of the attribute
    :return: the canonic name
    """
    attribute_colset_prefix = get_named_entity_colset_prefix(attribute_id)
    attribute_last_observation_colset_name = attribute_colset_prefix + "_LAST"
    return attribute_last_observation_colset_name


def get_activity_eaval_colset_name(act_id):
    """
    Canonic naming scheme for event colsets.

    :param act_id: the id of the activity
    :return: the canonic name
    """
    activity_colset_prefix = get_named_entity_colset_prefix(act_id)
    activity_eaval_colset_name = activity_colset_prefix + "_EAVAL"
    return activity_eaval_colset_name


class ColsetManager:
    colset_map: Colset_Map
    object_colsets: []
    event_colsets: []
    event_colsets_by_activity: dict
    additional_standard_colsets: []
    timed_id_colset: Colset
    parsed_colsets: set

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

    def add_event_id_colset(self):
        """
        Add an unambiguous colset to describe a token just with a case identifier
        """
        self.__add_alias_colset(Standard_Colsets.STRING.value, EVENTID_COLSET_NAME, timed=False)

    def add_timedint_colset(self):
        """
        Add a colset for timed integers
        """
        self.__add_alias_colset(Standard_Colsets.INT.value, TIMEDINT_COLSET_NAME, timed=True)

    def get_real_colset(self):
        """
        Get the unique real colset
        """
        return self.colset_map.colsets_by_name[get_real_colset_name()]

    def get_event_id_colset(self) -> Colset:
        """
        Get the unique case_id colset to describe a token just with a case identifier
        :return: the case_id colset
        """
        return self.colset_map.colsets_by_name[EVENTID_COLSET_NAME]

    def get_timed_int_colset(self) -> Colset:
        """
        Get the unique case_id colset to describe a token just with a case identifier
        :return: the case_id colset
        """
        return self.colset_map.colsets_by_name[TIMEDINT_COLSET_NAME]

    def add_activity_and_attribute_colsets(self,
                                           activities: list[CPM_Activity],
                                           attributes: list[CPM_Attribute],
                                           attributes_with_last_observations: list[CPM_Attribute],
                                           attributes_with_system_aggregations: list[CPM_Attribute],
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
        for attr in attributes:
            self.add_attribute_domain_colset(attr)
        for act in activities:
            act_attribute_ids = [
                attribute_id for attribute_id in
                attribute_activities.get_attribute_ids_for_activity_id(act.get_id())]
            self.add_activity_colset(act, act_attribute_ids)
        for attr in attributes_with_last_observations:
            attribute_id = attr.get_id()
            act = attribute_activities.get_activity_for_attribute_id(attribute_id)
            leading_type = act.get_leading_type()
            self.add_attribute_last_observation_colset(attr.get_id(), leading_type)
        for attr in attributes_with_system_aggregations:
            attribute_id = attr.get_id()
            act = attribute_activities.get_activity_for_attribute_id(attribute_id)
            leading_type = act.get_leading_type()
            self.add_attribute_all_observations_colset(attribute_id, leading_type)
            self.add_attribute_observations_list_colset(attribute_id)

    def add_activity_colset(self, activity: CPM_Activity, attribute_ids: list[str]):
        """
        Add a colset that describes an event of that activity
        :param activity_id:  the id of the activity
        :param attribute_ids:  all attributes of that activity
        """
        activity_id = activity.get_id()
        activity_eaval_colset_name = get_activity_eaval_colset_name(activity_id)
        attribute_domain_colsets = [
            self.colset_map.colsets_by_name[get_attribute_domain_colset_name(attribute_id)]
            for attribute_id in attribute_ids
        ]
        self.__add_product_colset(activity_eaval_colset_name, attribute_domain_colsets)

    def add_attribute_last_observation_colset(self, attribute_id: str, leading_type: ObjectType):
        """
        Create the colset to describe the last observed value of an attribute at each case.

        :param attribute_id: the id of the attribute
        :return: the colset
        """
        object_type_id_colset = self.get_object_type_ID_colset(leading_type)
        attribute_domain_colset = self.colset_map.colsets_by_name[get_attribute_domain_colset_name(attribute_id)]
        attribute_list_colset_name = get_attribute_list_colset_name(attribute_id)
        attribute_list_colset = self.__add_list_colset(attribute_list_colset_name, attribute_domain_colset)
        attribute_last_observation_colset_name = get_attribute_last_observation_colset_name(attribute_id)
        colset = self.__add_product_colset(attribute_last_observation_colset_name, [
            object_type_id_colset, attribute_list_colset
        ])  # , timed=True)
        return colset

    def add_attribute_context_observation_colset(self, attribute_id: str, leading_type: ObjectType):
        """
        Create the colset to describe all observed values of an attribute in the system.

        :param attribute_id: the id of the attribute
        :return: the colset
        """
        # TODO: just use the id. factor out case attributes we want to use to some static place.
        object_type_colset = self.get_object_type_colset(leading_type)
        attribute_domain_colset = self.colset_map.colsets_by_name[get_attribute_domain_colset_name(attribute_id)]
        timestamp_colset = self.get_real_colset()
        attribute_context_observations_colset_name = get_attribute_context_observation_colset_name(attribute_id)
        colset = self.__add_product_colset(attribute_context_observations_colset_name, [
            object_type_colset, timestamp_colset, attribute_domain_colset
        ])  # , timed=True)
        return colset

    def add_attribute_all_observations_colset(self, attribute_id: str, leading_type: ObjectType):
        context_observation_colset = self.add_attribute_context_observation_colset(attribute_id, leading_type)
        attribute_all_observations_colset_name = get_attribute_all_observations_colset_name(attribute_id)
        colset = self.__add_list_colset(attribute_all_observations_colset_name, context_observation_colset)
        return colset

    def add_attribute_observations_list_colset(self, attribute_id: str):
        attribute_domain_colset = self.colset_map.colsets_by_name[
            get_attribute_domain_colset_name(attribute_id)
        ]
        attribute_observations_list_colset_name = get_attribute_observations_list_colset_name(attribute_id)
        colset = self.__add_list_colset(attribute_observations_list_colset_name, attribute_domain_colset)

    def add_attribute_domain_colset(self, attribute: CPM_Attribute):
        """
        Create the colset to describe the domain (admissible values) of an attribute.

        :param attribute_id: the id of the attribute
        :param domain_colset_name: the domain for which this colset is an alias (e.g., string, int)
        :return: the colset
        """
        attribute_id = attribute.get_id()
        colset_name = get_attribute_domain_colset_name(attribute_id)
        attribute_domain = attribute.get_domain()
        colset = self.add_domain_colset(attribute_domain, colset_name)
        return colset

    def __add_list_colset(self, colset_name, subcol, timed: bool = False):
        """
        Create a colset of list type.

        :param colset_name: the name of the new colset
        :param subcol: the colset to be embedded into a list structure
        :return: the list colset
        """
        colset_id = self.cpn_id_manager.give_ID()
        colset = Colset(colset_id, colset_name, colset_type=Colset_Type.LIST, subcols=[subcol], timed=timed)
        self.__add_colset(colset)
        return colset

    def __add_product_colset(self, colset_name, subcols, timed=False):
        """
        Create a product colset for multiple colsets.

        :param colset_name: the name of the new product colset
        :param subcols: one or more colsets for which the product colset is to be created
        :return: the product colset
        """
        colset_id = self.cpn_id_manager.give_ID()
        colset = Colset(colset_id, colset_name, Colset_Type.PRODUCT, subcols, timed=timed)
        self.__add_colset(colset)
        return colset

    def __add_record_colset(self, colset_name: str, subcols: list[Colset], timed=False):
        """
        Create a colset for multiple colsets where each sub-colset is accessible by "dot notation" (e.g. t.X)

        :param colset_name: the name of the new record colset
        :param subcols: one or more colsets for which the record colset is to be created
        :return: the record colset
        """
        colset_id = self.cpn_id_manager.give_ID()
        colset = Colset(colset_id, colset_name, Colset_Type.RECORD, subcols, timed=timed)
        self.__add_colset(colset)
        return colset

    def __add_colset(self, colset):
        """
        Add a new colset to this object (ColsetManager) to be managed.

        :param colset: the colset to be added
        """
        self.colset_map.add(colset)

    def __add_alias_colset(self, colset_old_name, alias, timed=False):
        """
        Create a colset that is an alias of a different colset.

        :param colset_old_name: the name for which the alias is to be created
        :param alias: the new name
        :return: the alias colset
        """
        colset_id = self.cpn_id_manager.give_ID()
        colset_old: Colset = self.colset_map.colsets_by_name[colset_old_name]
        colset_new = Colset(colset_id, alias, colset_old.colset_type, [colset_old], timed=timed)
        self.__add_colset(colset_new)
        return colset_new

    def __add_with_colset(self, colset_name, labels, timed=False):
        colset_id = self.cpn_id_manager.give_ID()
        colset = WithColset(colset_id, colset_name, labels, timed)
        self.__add_colset(colset)
        return colset

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
            self.colset_vars_map[colset_name] = list()
        vars_count = len(self.colset_vars_map[colset_name]) + 1
        var_name = "v_" + var_name
        if vars_count > 1:
            var_name = var_name + "_" + str(vars_count)
        self.colset_vars_map[colset_name].append(var_name)
        self.var_name_roots = list(set(self.var_name_roots + [lower_name]))

    def get_one_var(self, colset_name: str) -> str:
        """
        Get one variable for a colset.

        :param colset_name: the name of the colset
        :return: a variable
        """
        if colset_name not in self.colset_vars_map:
            self.colset_vars_map[colset_name] = []
            self.__make_variable_for_colset(colset_name)
        colset_vars = self.colset_vars_map[colset_name]
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
        if n <= number:
            for i in range(number - n):
                self.__make_variable_for_colset(colset_name)
        colset_vars = self.colset_vars_map[colset_name]
        return colset_vars[:number]

    def add_object_type_ID_colset(self, ot: ObjectType):
        self.__add_alias_colset(Standard_Colsets.STRING.value, get_object_type_ID_colset_name(ot), timed=True)

    def get_object_type_ID_colset(self, ot: ObjectType):
        return self.colset_map.colsets_by_name[get_object_type_ID_colset_name(ot)]

    def add_object_type_ID_list_colset(self, ot: ObjectType):
        self.__add_list_colset(get_object_type_ID_list_colset_name(ot), self.get_object_type_ID_colset(ot))

    def get_object_type_ID_list_colset(self, ot: ObjectType):
        return self.colset_map.colsets_by_name[get_object_type_ID_list_colset_name(ot)]

    def add_object_type_colset(self, ot, ot_struct: ObjectTypeStructure):
        sorted_relations = ot_struct.get_sorted_relations(ot)
        sub_colsets = [self.get_object_type_ID_colset(ot), self.get_timed_int_colset()]
        for (m, ot2) in sorted_relations:
            if m is Multiplicity.ONE:
                sub_colsets.append(self.get_object_type_ID_colset(ot2))
            else:
                sub_colsets.append(self.get_object_type_ID_list_colset(ot2))
        self.__add_product_colset(get_object_type_colset_name(ot),
                                  sub_colsets,
                                  timed=True)

    def get_object_type_colset(self, ot):
        return self.colset_map.colsets_by_name[get_object_type_colset_name(ot)]

    def add_object_type_list_colset(self, ot):
        self.__add_list_colset(get_object_type_list_colset_name(ot), self.get_object_type_colset(ot), timed=True)

    def get_object_type_list_colset(self, ot):
        return self.colset_map.colsets_by_name[get_object_type_list_colset_name(ot)]

    def get_subcol_index_by_names(self, colset_name, subcolset_name):
        colset = self.colset_map.colsets_by_name[colset_name]
        subcolset = self.colset_map.colsets_by_name[subcolset_name]
        index = colset.subcols.index(subcolset)
        return index

    def get_all_attribute_domain_colset_vars(self, attrs: list[CPM_Attribute]):
        return [self.get_one_var(get_attribute_domain_colset_name(attr.get_id())) for attr in attrs]

    def get_all_attribute_domain_colset_names(self, attrs: list[CPM_Attribute]):
        return [get_attribute_domain_colset_name(attr.get_id()) for attr in attrs]

    def add_domain_colset(self, domain: CPM_Domain, colset_name=None):
        attribute_domain_type = domain.domain_type
        if colset_name is None:
            colset_name = get_domain_colset_name(domain)
        if colset_name in self.colset_map.colsets_by_name:
            return self.colset_map.colsets_by_name[colset_name]
        if attribute_domain_type is CPM_Attribute_Domain_Type.CATEGORICAL:
            domain: CPM_Categorical_Domain
            labels = domain.get_labels()
            colset = self.__add_with_colset(colset_name, labels)
        elif attribute_domain_type in CPM_Attribute_Domain_Type.get_timing_domain_types():
            colset = self.__add_alias_colset(get_real_colset_name(), colset_name)
        else:
            raise NotImplementedError()
        return colset

    def add_domain_colsets(self, domains: list[CPM_Domain]):
        for domain in domains:
            self.add_domain_colset(domain)
