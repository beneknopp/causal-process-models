import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element

from causal_model.causal_process_model import CausalProcessModel
from causal_model.causal_process_structure import CPM_Categorical_Attribute
from process_model.petri_net import SimplePetriNet
from simulation_model.cpn_utils.cpn_transition import CPN_Transition
from simulation_model.functions import get_all_standard_functions_ordered_sml, get_event_writer_sml, \
    get_activity_event_writer_name, get_eaval2list_converter_sml, get_eaval2list_converter_name, \
    get_label_to_string_converter_sml, get_label_to_string_converter_name, get_activity_event_table_initializer_name, \
    get_activity_event_table_initializer_sml, get_all_timing_functions_ordered_sml, get_all_event_functions_ordered_sml
from simulation_model.simulation_parameters import SimulationParameters
from simulation_model.timing import ActivityTimingManager, ProcessTimeCategory
from simulation_model.cpn_utils.cpn import CPN
from simulation_model.colset import ColsetManager, Colset_Type, Colset, WithColset
from simulation_model.control_flow import ControlFlowManager
from simulation_model.cpn_utils.xml_utils.cpn_id_managment import CPN_ID_Manager
from simulation_model.cpn_utils.xml_utils.page import Page


class CPM_CPN_Converter:

    def __init__(self,
                 cpn_template_path: str,
                 petriNet: SimplePetriNet,
                 causalModel: CausalProcessModel,
                 simulationParameters: SimulationParameters
                 ):
        self.tree = ET.parse(cpn_template_path)
        self.root = self.tree.getroot()
        self.mainpage = self.root.find("cpnet").find("page")
        self.subpages = []
        # self.portsock_map = dict()
        cpn_id_manager = CPN_ID_Manager(open(cpn_template_path).read())
        self.cpn_id_manager = cpn_id_manager
        self.colset_manager = ColsetManager(cpn_id_manager)
        self.controlflow_manager = ControlFlowManager(
            cpn_id_manager, petriNet, causalModel, simulationParameters, self.colset_manager
        )
        self.initial_places = {}
        self.new_colsets = []
        self.event_places_by_activity_name = dict()
        self.schema_generation_functions = dict()
        self.transition_substitutions = dict()
        self.port_sock_map = dict()
        self.other_functions = []
        self.uses = []
        self.petriNet = petriNet
        self.causalModel = causalModel
        self.simulationParameters = simulationParameters

    def convert(self):
        self.__initialize_activities_and_attributes()
        self.__make_colsets()
        self.__make_colset_variables()
        self.__merge_nets()
        self.__make_case_generator()
        self.__add_timing()
        self.__add_actions()
        self.__build_dom()

    def export(self, outpath):
        ET.indent(self.tree, space="\t", level=0)
        self.tree.write(outpath, encoding="utf-8")
        preamble = '<?xml version="1.0" encoding="iso-8859-1"?>' + \
                   '<!DOCTYPE workspaceElements PUBLIC "-//CPN//DTD CPNXML 1.0//EN" "http://cpntools.org/DTD/6/cpn.dtd">'
        xmlstring = open(outpath, "r").read()
        xmlstring = preamble + xmlstring
        # TODO
        hotfix = xmlstring.replace("&amp;", "&")
        f = open(outpath, "w")
        f.write(hotfix)
        f.close()

    def __initialize_activities_and_attributes(self):
        self.__activities = self.causalModel.get_activities()
        self.__attributes = self.causalModel.get_attributes()
        self.__attributeActivities = self.causalModel.get_attribute_activities()
        self.__expand_empty_activities()

    def __expand_empty_activities(self):
        """
        There may be labels in the Petri net that are not described in the causal model.
        Add an activity without attributes for those.

        :return: the complete list of activities after expansion
        """
        petri_net = self.petriNet
        causal_model = self.causalModel
        pn_labels = petri_net.get_activities()
        cm_acts = causal_model.get_activities()
        cm_labels = [act.get_name() for act in cm_acts]
        new_labels = set([l for l in pn_labels if l not in cm_labels])
        for l in new_labels:
            causal_model.add_activity(activity_name=l, activity_id=l)
        all_acts = causal_model.get_activities()
        return all_acts

    def __get_dom_block_element(self, name):
        global_blocks = self.root.find("cpnet").find("globbox").findall("block")
        el: Element = list(filter(lambda child: child.find("id").text == name, global_blocks))[0]
        return el

    def __make_colsets(self):
        activity_ids = [act.get_id() for act in self.__activities]
        attribute_ids = [attr.get_id() for attr in self.__attributes]
        attributes_with_last_observations = [
            attr.get_id() for attr in
            self.causalModel.get_attributes_with_non_aggregated_dependencies()]
        attributes_with_system_aggregations = [
            attr.get_id() for attr in
            self.causalModel.get_attributes_with_aggregated_dependencies()]
        standard_declarations_element = self.__get_dom_block_element("Standard declarations")
        self.colset_manager.parse_standard_colsets(standard_declarations_element)
        self.colset_manager.add_case_id_colset()
        self.colset_manager.add_event_id_colset()
        self.colset_manager.add_timedint_colset()
        self.colset_manager.add_activity_and_attribute_colsets(
            activity_ids=activity_ids,
            attributes=self.__attributes,
            attribute_activities=self.__attributeActivities,
            attributes_with_last_observations=attributes_with_last_observations,
            attributes_with_system_aggregations=attributes_with_system_aggregations
        )

    def __make_colset_variables(self):
        self.colset_manager.make_variables()

    def __make_case_generator(self):
        self.controlflow_manager.make_case_generator()

    def __merge_nets(self):
        self.controlflow_manager.merge_models()

    def __build_dom(self):
        self.__build_colsets()
        self.__build_variables()
        self.__build_petri_net()
        self.__build_functions()

    def __build_colsets(self):
        for colset in self.colset_manager.get_ordered_colsets():
            if colset not in self.colset_manager.parsed_colsets:
                block = self.__get_dom_block_element(
                    "Standard declarations"
                )
                self.__build_colset(block, colset)

    def __build_variables(self):
        globbox = self.root.find("cpnet").find("globbox")
        var_block = ET.SubElement(globbox, "block")
        var_block_id = self.cpn_id_manager.give_ID()
        var_block.set("id", var_block_id)
        id_child = ET.SubElement(var_block, "id")
        id_child.text = "Variables"
        colset_vars_map = self.colset_manager.colset_vars_map
        for colset_name, varset in colset_vars_map.items():
            self.__build_colset_vars(var_block, colset_name, varset)

    def __build_petri_net(self):
        places = self.controlflow_manager.get_cpn_places()
        transitions = self.controlflow_manager.get_cpn_transitions()
        arcs = self.controlflow_manager.get_cpn_arcs()
        for node in places + transitions + arcs:
            node.to_DOM_Element(self.mainpage)
        for subpage in self.subpages:
            subpage: Page
            # subpage.scale(2.0)
            subpage.to_DOM_Element(self.root.find("cpnet"))

    def __build_colset(self, parent: Element, colset: Colset):
        colset_element = ET.SubElement(parent, "color")
        colset_element_id = self.cpn_id_manager.give_ID()
        colset_element.set("id", colset_element_id)
        id_element = ET.SubElement(colset_element, "id")
        id_element.text = colset.colset_name
        if colset.timed:
            ET.SubElement(colset_element, "timed")
        if colset.colset_type == Colset_Type.PRODUCT:
            product_element = ET.SubElement(colset_element, "product")
            for subcol in colset.subcols:
                factor_element = ET.SubElement(product_element, "id")
                factor_element.text = subcol.colset_name
        elif colset.colset_type == Colset_Type.LIST:
            list_element = ET.SubElement(colset_element, "list")
            list_id_element = ET.SubElement(list_element, "id")
            list_id_element.text = colset.subcols[0].colset_name
        elif colset.colset_type == Colset_Type.WITH:
            colset: WithColset
            enum_element = ET.SubElement(colset_element, "enum")
            for label in colset.labels:
                id_element = ET.SubElement(enum_element, "id")
                id_element.text = label
        elif len(colset.subcols) == 1:
            alias_element = ET.SubElement(colset_element, "alias")
            alias_id_element = ET.SubElement(alias_element, "id")
            alias_id_element.text = colset.subcols[0].colset_name
        layout_element = ET.SubElement(colset_element, "layout")
        layout_element.text = colset.get_layout()

    def __build_colset_vars(self, var_block, colset_name, varset):
        var_element = ET.SubElement(var_block, "var")
        var_element_id = self.cpn_id_manager.give_ID()
        var_element.set("id", var_element_id)
        type_element = ET.SubElement(var_element, "type")
        type_id_element = ET.SubElement(type_element, "id")
        type_id_element.text = colset_name
        layout = "var "
        for var in varset:
            var_child = ET.SubElement(var_element, "id")
            var_child.text = var
            layout = layout + var + ", "
        layout = layout[:-2] + ": " + colset_name + ";"
        layout_element = ET.SubElement(var_element, "layout")
        layout_element.text = layout

    def __build_functions(self):
        globbox = self.root.find("cpnet").find("globbox")
        fun_block = ET.SubElement(globbox, "block")
        fun_block_id = self.cpn_id_manager.give_ID()
        fun_block.set("id", fun_block_id)
        id_child = ET.SubElement(fun_block, "id")
        id_child.text = "Functions"
        all_functions = \
            get_all_standard_functions_ordered_sml() + \
            get_all_timing_functions_ordered_sml({
                ProcessTimeCategory.SERVICE: self.simulationParameters.service_time_density,
                ProcessTimeCategory.ARRIVAL: self.simulationParameters.case_arrival_density
            }) + \
            get_all_event_functions_ordered_sml() + \
            self.causalModel.get_valuation_functions_sml()
        for attribute in self.__attributes:
            if not isinstance(attribute, CPM_Categorical_Attribute):
                continue
            attribute: CPM_Categorical_Attribute
            domain_colset_name = self.colset_manager.get_attribute_domain_colset_name(attribute.get_id())
            l2s_name = get_label_to_string_converter_name(attribute)
            l2s_sml = get_label_to_string_converter_sml(attribute, domain_colset_name)
            all_functions.append((l2s_name, l2s_sml))
        for activity in self.__activities:
            act_id = activity.get_id()
            act_name = activity.get_name()
            eaval_colset_name = self.colset_manager.get_activity_eaval_colset_name(act_id)
            eaval_to_list_converter_name = get_eaval2list_converter_name(act_id)
            attributes = self.causalModel.get_attributes_for_activity_id(act_id)
            attribute_names = [attr.get_name() for attr in attributes]
            eaval_to_list_converter_sml = get_eaval2list_converter_sml(
                act_id, eaval_colset_name, attributes)
            event_writer_name = get_activity_event_writer_name(act_id)
            event_writer_sml = get_event_writer_sml(act_id, act_name, eaval_colset_name)
            event_initializer_name = get_activity_event_table_initializer_name(act_id)
            event_initializer_sml  = get_activity_event_table_initializer_sml(act_id, attribute_names)
            all_functions.append((event_initializer_name, event_initializer_sml))
            all_functions.append((eaval_to_list_converter_name, eaval_to_list_converter_sml))
            all_functions.append((event_writer_name, event_writer_sml))
        for act in self.__activities:
            act_name = act.get_name()
            timing = self.simulationParameters.activity_timing_manager.\
                get_activity_timing(act_name)
            execution_delay = timing.execution_delay
            exdelay_name = execution_delay.get_function_name_SML()
            exdelay_string = execution_delay.get_all_SML()
            all_functions.append((exdelay_name, exdelay_string))
        ca_rate = self.simulationParameters.case_arrival_rate
        all_functions.append((ca_rate.get_function_name_SML(), ca_rate.get_all_SML()))
        for fun_name, fun_string in all_functions:
            fun_element = ET.SubElement(fun_block, "ml")
            fun_element.text = fun_string
            layout_element = ET.SubElement(fun_element, "layout")
            layout_element.text = fun_string
            fun_element.set("id", self.cpn_id_manager.give_ID())

    def __add_timing(self):
        self.controlflow_manager.add_timing()

    def __add_actions(self):
        self.controlflow_manager.add_iostream()
        self.controlflow_manager.add_table_initializing()
