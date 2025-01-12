import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element

from pandas import DataFrame

from causal_model.causal_process_model import CausalProcessModel
from causal_model.causal_process_structure import CPM_Categorical_Attribute
from object_centric.object_centric_petri_net import ObjectCentricPetriNet as OCPN
from object_centric.object_centricity_management import ObjectCentricityManager
from object_centric.object_type_structure import ObjectTypeStructure, ObjectType
from simulation_model.cpn_utils.cpn_transition import CPN_Transition
from simulation_model.functions import get_all_standard_functions_ordered_sml, get_event_writer_sml, \
    get_activity_event_writer_name, get_eaval2list_converter_sml, get_eaval2list_converter_name, \
    get_label_to_string_converter_sml, get_label_to_string_converter_name, get_activity_event_table_initializer_name, \
    get_activity_event_table_initializer_sml, get_all_timing_functions_ordered_sml, get_all_event_functions_ordered_sml
from simulation_model.simulation_parameters import SimulationParameters
from simulation_model.timing import ProcessTimeCategory
from simulation_model.colset import ColsetManager, Colset_Type, Colset, WithColset, get_attribute_domain_colset_name, \
    get_object_type_colset_name, get_object_type_ID_colset_name, get_object_type_ID_list_colset_name
from simulation_model.control_flow.control_flow_manager import ControlFlowManager
from simulation_model.cpn_utils.xml_utils.cpn_id_managment import CPN_ID_Manager
from simulation_model.cpn_utils.xml_utils.page import Page


class CPM_CPN_Converter:

    def __init__(self,
                 cpn_template_path: str,
                 petriNet: OCPN,
                 causalModel: CausalProcessModel,
                 objectTypeStructure: ObjectTypeStructure,
                 simulationParameters: SimulationParameters,
                 initialMarking: dict[ObjectType, DataFrame],
                 model_name: str
                 ):
        self.model_name = model_name
        self.tree = ET.parse(cpn_template_path)
        self.root = self.tree.getroot()
        self.mainpage = self.root.find("cpnet").find("page")
        self.subpages = []
        # self.portsock_map = dict()
        cpn_id_manager = CPN_ID_Manager(open(cpn_template_path).read())
        self.cpn_id_manager = cpn_id_manager
        self.colset_manager = ColsetManager(cpn_id_manager)
        self.objectcentricity_manager = ObjectCentricityManager(
            cpn_id_manager, petriNet, objectTypeStructure, self.colset_manager
        )
        self.controlflow_manager = ControlFlowManager(
            cpn_id_manager, petriNet, causalModel, simulationParameters, self.objectcentricity_manager,
            self.colset_manager, initialMarking
        )
        self.petriNet = petriNet
        self.causalModel = causalModel
        self.objectTypeStructure = objectTypeStructure
        self.initialMarking = initialMarking
        self.simulationParameters = simulationParameters

    def convert(self):
        self.__initialize_activities_and_attributes()
        self.__make_colsets()
        self.__make_colset_variables()
        self.__merge_nets()
        self.__make_object_type_synchronization()
        self.__make_case_terminator()
        self.__add_actions()
        self.__add_timing()
        self.__build_dom()

    def export(self, model_outpath):
        ET.indent(self.tree, space="\t", level=0)
        self.tree.write(model_outpath, encoding="utf-8")
        preamble = '<?xml version="1.0" encoding="iso-8859-1"?>' + \
                   '<!DOCTYPE workspaceElements PUBLIC "-//CPN//DTD CPNXML 1.0//EN" "http://cpntools.org/DTD/6/cpn.dtd">'
        xmlstring = open(model_outpath, "r").read()
        xmlstring = preamble + xmlstring
        # TODO
        hotfix = xmlstring.replace("&amp;", "&")
        f = open(model_outpath, "w")
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
            causal_model.add_activity(activity_name=l)
        all_acts = causal_model.get_activities()
        return all_acts

    def __get_dom_block_element(self, name):
        global_blocks = self.root.find("cpnet").find("globbox").findall("block")
        el: Element = list(filter(lambda child: child.find("id").text == name, global_blocks))[0]
        return el

    def __make_colsets(self):
        attributes_with_last_observations = [
            attr for attr in self.causalModel.get_attributes_with_non_aggregated_dependencies()
        ]
        attributes_with_system_aggregations = [
            attr for attr in self.causalModel.get_attributes_with_aggregated_dependencies()]
        standard_declarations_element = self.__get_dom_block_element("Standard declarations")
        self.colset_manager.parse_standard_colsets(standard_declarations_element)
        self.colset_manager.add_event_id_colset()
        self.colset_manager.add_timedint_colset()
        for ot in self.objectTypeStructure.get_object_types():
            self.colset_manager.add_object_type_ID_colset(ot)
            self.colset_manager.add_object_type_ID_list_colset(ot)
        for ot in self.objectTypeStructure.get_object_types():
            self.colset_manager.add_object_type_colset(ot, self.objectTypeStructure)
            self.colset_manager.add_object_type_list_colset(ot)
        self.colset_manager.add_activity_and_attribute_colsets(
            activities=self.__activities,
            attributes=self.__attributes,
            attribute_activities=self.__attributeActivities,
            attributes_with_last_observations=attributes_with_last_observations,
            aggregation_domains=self.causalModel.get_aggregation_domains(),
            attributes_with_system_aggregations=attributes_with_system_aggregations
        )
        self.colset_manager.add_domain_colsets(
            self.causalModel.get_all_valuation_parameter_domains()
        )

    def __make_colset_variables(self):
        self.colset_manager.make_variables()

    def __make_case_terminator(self):
        self.controlflow_manager.make_case_terminator()

    def __merge_nets(self):
        self.controlflow_manager.merge_models()

    def __build_dom(self):
        self.__build_colsets()
        self.__build_constants()
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


    def __build_constants(self):
        const_block = self.__make_block("Constants")
        for object_type in self.objectTypeStructure.get_object_types():
            initmark_name = "initmark_" + object_type.get_id()
            initmark = self.__get_initial_marking(object_type)
            const_element = ET.SubElement(const_block, "ml")
            const_element.text = "val {0} = {1}".format(
                initmark_name,
                initmark
            )
            const_element.set("id", self.cpn_id_manager.give_ID())


    def __build_variables(self):
        globbox = self.root.find("cpnet").find("globbox")
        var_block = ET.SubElement(globbox, "block")
        var_block_id = self.cpn_id_manager.give_ID()
        var_block.set("id", var_block_id)
        id_child = ET.SubElement(var_block, "id")
        id_child.text = "Variables"
        colset_vars_map = self.colset_manager.colset_vars_map
        handled_vars = set()
        for colset_name, varset in colset_vars_map.items():
            varset = [var for var in varset if var not in handled_vars]
            self.__build_colset_vars(var_block, colset_name, varset)
            handled_vars = set(list(varset) + list(handled_vars))

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

    def __make_block(self, name):
        globbox = self.root.find("cpnet").find("globbox")
        block = ET.SubElement(globbox, "block")
        block_id = self.cpn_id_manager.give_ID()
        block.set("id", block_id)
        id_child = ET.SubElement(block, "id")
        id_child.text = name
        return block

    def __build_functions_in_block(self, functions, block):
        for fun_name, fun_string in functions:
            fun_element = ET.SubElement(block, "ml")
            fun_element.text = fun_string
            layout_element = ET.SubElement(fun_element, "layout")
            layout_element.text = fun_string
            fun_element.set("id", self.cpn_id_manager.give_ID())

    def __build_basic_functions(self):
        fun_block = self.__make_block("Basic Functions")
        all_functions = \
            get_all_standard_functions_ordered_sml() + \
            get_all_timing_functions_ordered_sml({
                ProcessTimeCategory.SERVICE: self.simulationParameters.service_time_density,
                ProcessTimeCategory.ARRIVAL: self.simulationParameters.case_arrival_density
            }) + \
            get_all_event_functions_ordered_sml() + \
            self.causalModel.get_valuation_functions_sml()
        self.__build_functions_in_block(all_functions, fun_block)

    def __build_attribute_functions(self):
        fun_block = self.__make_block("Attribute Functions")
        all_functions = []
        for attribute in self.__attributes:
            if not isinstance(attribute, CPM_Categorical_Attribute):
                continue
            attribute: CPM_Categorical_Attribute
            domain_colset_name = get_attribute_domain_colset_name(attribute.get_id())
            l2s_name = get_label_to_string_converter_name(attribute)
            l2s_sml = get_label_to_string_converter_sml(attribute, domain_colset_name)
            all_functions.append((l2s_name, l2s_sml))
        self.__build_functions_in_block(all_functions, fun_block)

    def __build_object_functions(self):
        fun_block = self.__make_block("Object Functions")
        ot_sml_functions = self.objectcentricity_manager.get_object_type_sml_functions()
        self.__build_functions_in_block(ot_sml_functions, fun_block)

    def __build_aggregation_logic_functions(self):
        fun_block = self.__make_block("Aggregation Logic Functions")
        selection_functions = self.causalModel.get_selection_functions_smls()
        aggregation_functions = self.causalModel.get_aggregation_functions_smls()
        self.__build_functions_in_block(selection_functions, fun_block)
        self.__build_functions_in_block(aggregation_functions, fun_block)

    def __build_activity_functions(self):
        fun_block = self.__make_block("Activity Functions")
        all_functions = []
        for activity in self.__activities:
            act_id = activity.get_id()
            act_name = activity.get_name()
            local_attributes = self.causalModel.get_local_attributes_for_activity_id(act_id)
            eaval_colset_names = self.colset_manager.get_all_attribute_domain_colset_names(local_attributes)
            eaval_to_list_converter_name = get_eaval2list_converter_name(act_id)

            attribute_names = [attr.get_name() for attr in local_attributes]
            eaval_to_list_converter_sml = get_eaval2list_converter_sml(
                act_id, local_attributes, eaval_colset_names)
            event_writer_name = get_activity_event_writer_name(act_id)
            start_time_attribute = self.causalModel.get_start_time_attribute_for_activity(activity)
            complete_time_attribute = self.causalModel.get_complete_time_attribute_for_activity(activity)
            return_start_time = self.causalModel.has_post_dependency(start_time_attribute)
            return_complete_time = self.causalModel.has_post_dependency(complete_time_attribute)
            event_writer_sml = get_event_writer_sml(
                act_id, act_name, eaval_colset_names, self.model_name)
            event_initializer_name = get_activity_event_table_initializer_name(act_id)
            event_initializer_sml = get_activity_event_table_initializer_sml(act_id, attribute_names, self.model_name)
            all_functions.append((event_initializer_name, event_initializer_sml))
            all_functions.append((eaval_to_list_converter_name, eaval_to_list_converter_sml))
            all_functions.append((event_writer_name, event_writer_sml))
        self.__build_functions_in_block(all_functions, fun_block)

    def __build_transition_code_functions(self):
        fun_block = self.__make_block("Code Functions")
        transition: CPN_Transition
        all_functions = []
        for transition in self.controlflow_manager.get_cpn_transitions():
            if transition.has_code():
                all_functions.append((transition.get_code_name(), transition.get_code_sml()))
        for act in self.__activities:
            act_name = act.get_name()
            timing = self.simulationParameters.activity_timing_manager. \
                get_activity_timing(act_name)
            execution_delay = timing.execution_delay
            exdelay_name = execution_delay.get_function_name_SML()
            exdelay_string = execution_delay.get_all_SML()
            all_functions.append((exdelay_name, exdelay_string))
        ca_rate = self.simulationParameters.case_arrival_rate
        all_functions.append((ca_rate.get_function_name_SML(), ca_rate.get_all_SML()))
        self.__build_functions_in_block(all_functions, fun_block)

    def __build_functions(self):
        self.__build_basic_functions()
        self.__build_attribute_functions()
        self.__build_object_functions()
        self.__build_aggregation_logic_functions()
        self.__build_activity_functions()
        self.__build_transition_code_functions()

    def __add_timing(self):
        self.controlflow_manager.add_timing()

    def __add_actions(self):
        self.controlflow_manager.add_iostream()
        self.controlflow_manager.add_table_initializing()

    def __make_object_type_synchronization(self):
        self.controlflow_manager.make_object_type_synchronization()

    def __get_initial_marking(self, object_type):
        initmark_df = self.initialMarking[object_type]
        to_1_relations = self.objectcentricity_manager.get_to_1_relations_for_object_type(object_type)
        to_N_relations = self.objectcentricity_manager.get_to_N_relations_for_object_type(object_type)
        object_type_1_colset_name = get_object_type_colset_name(object_type)
        index_to_object_type = {}
        for other_object_type in to_1_relations:
            object_type_2_id_colset_name = get_object_type_ID_colset_name(other_object_type)
            ot2_at_ot1_index = self.colset_manager.get_subcol_index_by_names(object_type_1_colset_name, object_type_2_id_colset_name)
            index_to_object_type[ot2_at_ot1_index] = other_object_type.get_name()
        for other_object_type in to_N_relations:
            object_type_2_id_list_colset_name = get_object_type_ID_list_colset_name(other_object_type)
            ot2_at_ot1_index = self.colset_manager.get_subcol_index_by_names(object_type_1_colset_name, object_type_2_id_list_colset_name)
            index_to_object_type[ot2_at_ot1_index] = other_object_type.get_name()

        list_of_object_token_prefixes = initmark_df.apply(
            lambda row: '("{0}",0,'.format(row["ocel_id"]), axis=1).tolist()
        list_of_object_token_suffixes = initmark_df.apply(
            lambda row: '{0})'.format(self.__initial_token_suffix_transformation(row, index_to_object_type)), axis=1).tolist()
        list_of_object_token_timestamps = initmark_df.apply(
            lambda row: str(round(row["ocel_time"])), axis=1).tolist()
        token_list = ["{0}{1}@{2}".format(
            list_of_object_token_prefixes[i],
            list_of_object_token_suffixes[i],
            list_of_object_token_timestamps[i]
        ) for i in range(len(initmark_df))]
        initmark = "[" + ",".join(token_list) + "]"
        return initmark

    def __initial_token_suffix_transformation(self, row, index_to_object_type):
        suffixes = []
        for index in sorted(list(index_to_object_type.keys())):
            related_objects = dict(row)[index_to_object_type[index]]
            if type(related_objects) is list:
                related_objects_str = "[" + ','.join(['"{0}"'.format(related_object) for related_object in related_objects]) + "]"
            else:
                related_objects_str = '"{0}"'.format(related_objects)
            suffixes.append(related_objects_str)
        return ",".join(suffixes)