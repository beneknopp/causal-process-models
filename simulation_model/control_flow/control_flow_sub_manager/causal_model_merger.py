from causal_model.aggregation_functions.aggregation_functions import AggregationFunction
from causal_model.causal_process_model import CausalProcessModel, AggregationSelection
from causal_model.causal_process_structure import CPM_Activity, CPM_Attribute, CPM_Domain_Type, \
    AttributeRelation
from object_centric.object_centric_petri_net import ObjectCentricPetriNetTransition as Transition, ObjectCentricPetriNet
from object_centric.object_type_structure import ObjectType
from simulation_model.colset import ColsetManager, get_attribute_all_observations_colset_name, \
    get_object_type_colset_name, get_object_type_ID_colset_name, get_attribute_domain_colset_name, \
    get_attribute_list_colset_name, get_attribute_last_observation_colset_name, \
    get_attribute_observations_list_colset_name, get_domain_colset_name

from simulation_model.control_flow.map import get_global_semaphore_place_name, ControlFlowMap, \
    get_control_place_id_case, get_control_place_id_event, get_attribute_global_last_observation_place_name, \
    get_attribute_global_all_observations_place_name, get_attribute_valuation_transition_name, \
    get_attribute_valuation_main_in_place_name, get_attribute_valuation_main_out_place_name, \
    get_preset_attribute_last_observation_place_name, get_aggregation_selection_transition_name, \
    get_control_selection_place_name, get_selected_values_place_name, get_aggregation_transition_name, \
    get_aggregated_values_place_name
from simulation_model.cpn_utils.cpn_arc import CPN_Arc
from simulation_model.cpn_utils.cpn_place import CPN_Place
from simulation_model.cpn_utils.cpn_transition import CPN_Transition, TransitionType
from simulation_model.cpn_utils.xml_utils.cpn_id_managment import CPN_ID_Manager
from simulation_model.functions import get_now_time_getter_name


class CausalModelMerger:

    def __init__(self,
                 cpn_id_manager: CPN_ID_Manager,
                 controlFlowMap: ControlFlowMap,
                 petriNet: ObjectCentricPetriNet,
                 causalModel: CausalProcessModel,
                 colsetManager: ColsetManager):
        self.cpn_id_manager = cpn_id_manager
        self.__controlFlowMap = controlFlowMap
        self.__petriNet = petriNet
        self.__causalModel = causalModel
        self.__colsetManager = colsetManager
        # remember the variable names in the event attribute value maps
        self.__eaval_parameter_tuples = {}

    def merge_in_causal_model(self):
        self.__make_causal_places()
        x, y = self.__controlFlowMap.get_node_coordinates(location=2)
        # place to make activity executions atomic (a critical section)
        semaphore_place = CPN_Place(
            get_global_semaphore_place_name(), x, y, self.cpn_id_manager,
            colset_name="INT",
            initmark="1"
        )
        self.__controlFlowMap.add_place(semaphore_place)
        cm_activities = self.__causalModel.get_activities()
        for act in cm_activities:
            act_name = act.get_name()
            act_transitions = self.__petriNet.get_transitions_with_label(act_name)
            t: Transition
            for t in act_transitions:
                self.__convert_activity_transition(t, act)

    def __make_causal_places(self):
        """
        Here, we add places to the net that contain "last observations" (lobs), and also places for aggregation.
        Each lobs place carries attribute values for one specific event attribute
        that is required for some non-aggregated causal dependency.
        Each aggregation place carries a list of attribute values for one specific attribute
        that is required for some aggregated causal dependency.
        """
        non_agg_attributes = self.__causalModel.get_attributes_with_non_aggregated_dependencies()
        agg_attributes = self.__causalModel.get_attributes_with_aggregated_dependencies()
        for attribute in non_agg_attributes:
            self.__make_last_observation_place(attribute)
        for attribute in agg_attributes:
            self.__make_all_observations_place(attribute)

    def __make_last_observation_place(self, attribute: CPM_Attribute):
        """
        Make the unique place in the net where the last observation of some event
        attribute is being monitored. Also, make sure a token is added upon case arrival.

        :param attribute: the attribute being monitored
        """
        lobs_place_name = get_attribute_global_last_observation_place_name(attribute.get_id())
        lobs_colset_name = get_attribute_last_observation_colset_name(
            attribute.get_id()
        )
        x, y = self.__controlFlowMap.get_node_coordinates()
        object_type = self.__causalModel.get_activity_for_attribute_id(attribute.get_id()).get_leading_type()
        object_type_var = self.__colsetManager.get_one_var(
            get_object_type_colset_name(object_type))
        p_LOBS = CPN_Place(lobs_place_name, x, y, self.cpn_id_manager, lobs_colset_name, False,
                           object_type=object_type)
        self.__controlFlowMap.add_lobs_place(p_LOBS, attribute)
        t_CASE_INIT = self.__controlFlowMap.get_case_initialization_transition(object_type)
        a_LOBS_INIT_EXPRESSION = "(#1 {0},[])".format(object_type_var)
        a_LOBS_INIT = CPN_Arc(self.cpn_id_manager, t_CASE_INIT, p_LOBS, a_LOBS_INIT_EXPRESSION)
        self.__controlFlowMap.add_arc(a_LOBS_INIT)

    def __make_all_observations_place(self, attribute: CPM_Attribute):
        """
        Make the unique place in the net where the all occurrences of some
        attributes are collected.

        :param attribute: the attribute being collected for the purpose of aggregation
        """
        allobs_place_name = get_attribute_global_all_observations_place_name(attribute.get_id())
        allobs_colset_name = get_attribute_all_observations_colset_name(
            attribute.get_id()
        )
        x, y = self.__controlFlowMap.get_node_coordinates()
        object_type = self.__causalModel.get_activity_for_attribute_id(attribute.get_id()).get_leading_type()
        p_ALLOBS = CPN_Place(allobs_place_name, x, y, self.cpn_id_manager, allobs_colset_name, False,
                             initmark="[]", object_type=object_type)
        self.__controlFlowMap.add_allobs_place(p_ALLOBS, attribute)

    def __convert_activity_transition(self, ocpn_transition: Transition, activity: CPM_Activity):
        """
        Activity transitions was split into two. Here, connect the two transitions and add logic.
        The first transition (start_t) is a controlling transition that makes sure that
        (a) the required objects can be found (possibly of multiple types around a leading object) and
        (b) the required attributes have been observed in the process.
        The second transition (end_t) conducts the effective event transaction, i.e., writing the event to the log
        along with the event attributes, object identifiers etc.
        In between the two transitions, we add steps for attribute valuations.

        :param ocpn_transition: the original OCPN transition
        :param activity: the CPM_Activity corresponding to the transition label
        """
        t_CONTROL = self.__controlFlowMap.get_control_transition_for_ocpn_transition(ocpn_transition)
        t_TRANSACT = self.__controlFlowMap.get_transaction_transition_for_ocpn_transition(ocpn_transition)
        control_p_case, control_p_event = self.__make_control_places(ocpn_transition)
        leading_type = ocpn_transition.get_leading_type()
        leading_type_var = self.__colsetManager.get_one_var(
            get_object_type_colset_name(leading_type))
        int_var = self.__colsetManager.get_one_var("INT")
        control_a1 = CPN_Arc(self.cpn_id_manager, t_CONTROL, control_p_case, leading_type_var)
        control_a2 = CPN_Arc(self.cpn_id_manager, control_p_case, t_TRANSACT, leading_type_var)
        self.__controlFlowMap.add_arc(control_a1)
        self.__controlFlowMap.add_arc(control_a2)
        control_b1 = CPN_Arc(self.cpn_id_manager, t_CONTROL, control_p_event, int_var)
        control_b2 = CPN_Arc(self.cpn_id_manager, control_p_event, t_TRANSACT, int_var)
        self.__controlFlowMap.add_arc(control_b1)
        self.__controlFlowMap.add_arc(control_b2)
        self.__add_attribute_logic(ocpn_transition, t_CONTROL, t_TRANSACT, activity)
        # Semaphore also carries a running event id
        sem = self.__controlFlowMap.cpn_places_by_name[get_global_semaphore_place_name()]
        sem_in = CPN_Arc(self.cpn_id_manager, sem, t_CONTROL, str(int_var))
        sem_out = CPN_Arc(self.cpn_id_manager, t_TRANSACT, sem, str(int_var) + " + 1")
        self.__controlFlowMap.add_arc(sem_in)
        self.__controlFlowMap.add_arc(sem_out)

    def __make_control_places(self, ocpn_transition: Transition) -> [CPN_Place, CPN_Place]:
        control_p_name_case = get_control_place_id_case(ocpn_transition)
        control_p_name_event = get_control_place_id_event(ocpn_transition)
        x = ocpn_transition.x + 300
        y = ocpn_transition.y
        leading_type = ocpn_transition.get_leading_type()
        control_p_case = CPN_Place(
            control_p_name_case, x, y, self.cpn_id_manager,
            get_object_type_colset_name(leading_type)
        )
        control_p_event = CPN_Place(control_p_name_event, x, y, self.cpn_id_manager, "INT")
        self.__controlFlowMap.add_place(control_p_case)
        self.__controlFlowMap.add_place(control_p_event)
        return control_p_case, control_p_event

    def __add_attribute_logic(self,
                              ocpn_transition: Transition,
                              t_CONTROL: CPN_Transition,
                              t_TRANSACT: CPN_Transition,
                              activity: CPM_Activity):
        # for each activity attribute, make a transition to valuate the attribute,
        # and feed it into the labeled transition
        # add connections w.r.t non-aggregated dependencies
        # TODO: add connections w.r.t aggregated dependencies
        attributes = self.__causalModel.get_attributes_for_activity_id(activity.get_id())
        standard_attributes = [
            attr for attr in attributes
            if not attr.get_domain_type() in CPM_Domain_Type.get_independent_domain_types()]
        timing_attributes = [
            attr for attr in attributes
            if attr.get_domain_type() in CPM_Domain_Type.get_timing_domain_types()]
        self.__add_system_observation_logic_for_attributes(attributes, activity, t_TRANSACT)
        self.__add_standard_attributes_logic(standard_attributes, ocpn_transition, t_CONTROL, t_TRANSACT,
                                             activity)
        self.__add_timing_attributes_logic(timing_attributes, t_TRANSACT, activity)

    def __add_standard_attributes_logic(self,
                                        attributes: list[CPM_Attribute],
                                        ocpn_transition: Transition,
                                        t_CONTROL: CPN_Transition,
                                        t_TRANSACT: CPN_Transition,
                                        activity: CPM_Activity
                                        ):
        transition_id = ocpn_transition.get_id()
        leading_type = activity.get_leading_type()
        # for each preset attribute, that is, each attribute on which some event attribute at the current
        # activity depends, we check whether a last observation exists (to guard the start transition of the
        # activity), and if it does exist, we query the last observation to be used during valuation.
        self.__current_transformed_transition_required_lobs_attributes = set()
        self.__current_transformed_transition_required_aggr_attributes = set()
        for i, attribute in enumerate(attributes):
            self.__collect_preset_attributes(attribute)
        self.__control_transition_for_last_observations(t_CONTROL, leading_type)
        # As we now iterate the event attributes to build control structures, we get the last observations
        # from the start transition guard.
        attribute_domain_vars = []
        attribute_list_vars = []
        for i, attribute in enumerate(attributes):
            x = ocpn_transition.x + 300
            y = ocpn_transition.y + 300 * (i + 1)
            valuated_attribute_place = self.__make_attribute_valuation_structure(
                activity, transition_id, t_CONTROL, attribute, x, y)
            attribute_domain_var = self.__colsetManager.get_one_var(
                get_attribute_domain_colset_name(attribute.get_id())
            )
            attribute_domain_vars.append(attribute_domain_var)
            global_lobs_place_name = get_attribute_global_last_observation_place_name(attribute.get_id())
            if global_lobs_place_name in self.__controlFlowMap.cpn_places_by_name:
                # attribute is observed (there are post-dependencies)
                # get two variables: the another variable for the old last observation
                attribute_list_var = self.__colsetManager.get_one_var(
                    get_attribute_list_colset_name(attribute.get_id())
                )
                attribute_list_vars.append(attribute_list_var)
            attribute_to_event = CPN_Arc(self.cpn_id_manager,
                                         valuated_attribute_place,
                                         t_TRANSACT,
                                         attribute_domain_var)
            self.__controlFlowMap.add_arc(attribute_to_event)
        object_type_id_var = self.__colsetManager.get_one_var(
            get_object_type_ID_colset_name(leading_type))
        self.__eaval_parameter_tuples[activity.get_name()] = [object_type_id_var] + attribute_domain_vars
        # distribute new last observations to global monitoring places
        for i, attribute in enumerate(attributes):
            global_lobs_place_name = get_attribute_global_last_observation_place_name(attribute.get_id())
            if global_lobs_place_name not in self.__controlFlowMap.cpn_places_by_name:
                # attribute is not observed (no post-dependencies)
                continue
            attribute_list_var_old = attribute_list_vars[i]
            attribute_domain_var_new = attribute_domain_vars[i]
            global_lobs_place = self.__controlFlowMap.cpn_places_by_name[
                global_lobs_place_name
            ]
            old_last_observation = "({0},{1})".format(
                object_type_id_var,
                attribute_list_var_old
            )
            new_last_observation = "({0},[{1}])".format(
                object_type_id_var,
                attribute_domain_var_new
            )
            lobs_old_arc = CPN_Arc(self.cpn_id_manager, global_lobs_place, t_TRANSACT, old_last_observation)
            lobs_new_arc = CPN_Arc(self.cpn_id_manager, t_TRANSACT, global_lobs_place, new_last_observation)
            self.__controlFlowMap.add_arc(lobs_old_arc)
            self.__controlFlowMap.add_arc(lobs_new_arc)

    def __collect_preset_attributes(self, attribute: CPM_Attribute):
        non_aggregated_preset = self.__causalModel.get_preset(attribute, aggregated=False)
        aggregated_preset = self.__causalModel.get_preset(attribute, aggregated=True)
        for r in non_aggregated_preset:
            self.__current_transformed_transition_required_lobs_attributes.add(r.get_in())
        for r in aggregated_preset:
            self.__current_transformed_transition_required_aggr_attributes.add(r.get_in())

    def __control_transition_for_last_observations(self, t_CONTROL: CPN_Transition, leading_type: ObjectType):
        lobs_attrs = list(self.__current_transformed_transition_required_lobs_attributes)
        lobs_colset_names = [
            get_attribute_list_colset_name(attr.get_id())
            for attr in lobs_attrs]
        all_preset_list_variables = [
            self.__colsetManager.get_one_var(preset_colset_name)
            for preset_colset_name in lobs_colset_names
        ]
        # for each preset attribute of some event attribute, ...
        leading_type_variable = self.__colsetManager.get_one_var(
            get_object_type_colset_name(leading_type)
        )
        leading_type_id_variable = self.__colsetManager.get_one_var(
            get_object_type_ID_colset_name(leading_type)
        )
        for i in range(len(lobs_attrs)):
            lobs_attr = lobs_attrs[i]
            preset_list_variable = all_preset_list_variables[i]
            # ...make back and forth arcs of the last observation place with the start transition
            global_lobs_place_name = get_attribute_global_last_observation_place_name(lobs_attr.get_id())
            global_lobs_place = self.__controlFlowMap.cpn_places_by_name[global_lobs_place_name]
            lobs_arc_inscription = "({0}, {1})".format(leading_type_id_variable, preset_list_variable)
            p_to_t = CPN_Arc(self.cpn_id_manager, global_lobs_place, t_CONTROL, lobs_arc_inscription)
            t_to_p = CPN_Arc(self.cpn_id_manager, t_CONTROL, global_lobs_place, lobs_arc_inscription)
            self.__controlFlowMap.add_arc(p_to_t)
            self.__controlFlowMap.add_arc(t_to_p)
            # ... make sure the activity can only be executed if there is a well-defined last observation
            # of the preset attribute.
            t_CONTROL.add_guard_conjunct("{0}=(#1 {1})".format(leading_type_id_variable, leading_type_variable))
            t_CONTROL.add_guard_conjunct("length({0})>0".format(preset_list_variable))

    def __make_attribute_valuation_structure(self, activity: CPM_Activity, transition_id: str,
                                             t_CONTROL: CPN_Transition, attr_VALUATED: CPM_Attribute, x=0.0, y=0.0) \
            -> CPN_Place:
        """
        For the activity of this transition, valuate one event attribute
        w.r.t the dependencies specified in the causal model.

        :param transition_id: Some identifier of this section (transition)
        :param t_CONTROL: The start transition of the activity section
        :param attribute_id: The ID of the attribute
        :param x: x-coordinate of transition in visual net
        :param y: y-coordinate of transition in visual net
        :returns The CPN_Place that will carry the valuation result
        """
        # make valuation transition and its guard
        preset = self.__causalModel.get_preset(attr_VALUATED)
        preset_domain_colset_names = []
        for r in preset:
            in_attribute = r.get_in()
            if r.is_aggregated():
                fagg: AggregationFunction = self.__causalModel.get_aggregation_function().relationsToAggregation[r]
                domain = fagg.output_domain
            else:
                domain = in_attribute.get_domain()
            preset_domain_colset_names.append(get_domain_colset_name(domain))
        preset_domain_variables = [
            self.__colsetManager.get_one_var(preset_colset_name)
            for preset_colset_name in preset_domain_colset_names
        ]
        attr_colset_name = get_attribute_domain_colset_name(attr_VALUATED.get_id())
        attr_variable = self.__colsetManager.get_one_var(attr_colset_name)
        valuation_transition_name = get_attribute_valuation_transition_name(transition_id, attr_VALUATED.get_id())
        valuation_call = self.__causalModel.get_attribute_valuations(). \
            get_attribute_valuation(attr_VALUATED.get_id()).get_call()
        valuation_guard = "[" + attr_variable + "=" + valuation_call(preset_domain_variables) + "]"
        t_VALUATE = CPN_Transition(TransitionType.SILENT, valuation_transition_name, x, y,
                                   self.cpn_id_manager,
                                   valuation_guard)
        self.__controlFlowMap.add_transition(t_VALUATE)
        # Add control place to preset (colset: UNIT) so that valuation happens only once
        main_control_place = CPN_Place(
            get_attribute_valuation_main_in_place_name(transition_id, attr_VALUATED.get_id()), x - 100, y,
            self.cpn_id_manager)
        main_control_arc1 = CPN_Arc(self.cpn_id_manager, t_CONTROL, main_control_place)
        main_control_arc2 = CPN_Arc(self.cpn_id_manager, main_control_place, t_VALUATE)
        self.__controlFlowMap.add_place(main_control_place)
        self.__controlFlowMap.add_arc(main_control_arc1)
        self.__controlFlowMap.add_arc(main_control_arc2)
        # connect dependencies: for each attribute, the last-observation-place with the start transition
        # add conjunct to the start transition guard (last observation need to be well-defined)
        # note that this can be redundant with other attributes at this transition
        # add place of preset attribute domain and connect it with valuation transition.
        for i, in_relation in enumerate(preset):
            if in_relation.is_aggregated():
                # we aggregate within the transition segment, no guarding of control transition required
                # but selection and aggreagation
                attr_AGGREGATED = in_relation.get_in()
                sagg = self.__causalModel.get_selection_function_for_relation(in_relation)
                fagg = self.__causalModel.get_aggregation_function_for_relation(in_relation)
                self.__add_aggregation_logic_for_attribute(
                    activity, attr_VALUATED, attr_AGGREGATED, t_CONTROL, t_VALUATE, sagg, fagg
                )
                continue
            # else:
            in_attr_id = in_relation.get_in().get_id()
            in_attr_colset_name = get_attribute_domain_colset_name(in_attr_id)
            in_attr_place_name = get_preset_attribute_last_observation_place_name(transition_id, in_attr_id)
            in_attr_variable = self.__colsetManager.get_one_var(in_attr_colset_name)
            preset_list_colset_name = get_attribute_list_colset_name(in_attr_id)
            lobs_place = CPN_Place(in_attr_place_name, x + 300, y - 300 * i, self.cpn_id_manager,
                                   in_attr_colset_name)
            self.__controlFlowMap.add_place(lobs_place)
            preset_list_variable = self.__colsetManager.get_one_var(preset_list_colset_name)
            # the expression to get the last observation: the head (hd) of the second element
            # the last_observation colset is a product colset and the second element is a list
            # carrying either the last observation or nothing
            lobs_expression = "hd({0})".format(preset_list_variable)
            start_to_lobs = CPN_Arc(self.cpn_id_manager, t_CONTROL, lobs_place, lobs_expression)
            lobs_to_vt = CPN_Arc(self.cpn_id_manager, lobs_place, t_VALUATE, in_attr_variable)
            self.__controlFlowMap.add_arc(start_to_lobs)
            self.__controlFlowMap.add_arc(lobs_to_vt)
        attr_domain_colset_name = get_attribute_domain_colset_name(attr_VALUATED.get_id())
        main_out_place = CPN_Place(
            get_attribute_valuation_main_out_place_name(transition_id, attr_VALUATED.get_id()), x + 100, y,
            self.cpn_id_manager,
            colset_name=attr_domain_colset_name)
        attr_domain_var = self.__colsetManager.get_one_var(attr_domain_colset_name)
        vt_to_mop = CPN_Arc(self.cpn_id_manager, t_VALUATE, main_out_place, attr_domain_var)
        self.__controlFlowMap.add_place(main_out_place)
        self.__controlFlowMap.add_arc(vt_to_mop)
        return main_out_place

    def __add_timing_attributes_logic(self,
                                      timing_attributes: list[CPM_Attribute],
                                      t_TRANSACT: CPN_Transition,
                                      activity: CPM_Activity
                                      ):
        """
        If the timestamps of this activity are used somewhere,
        distribute the observed timestamps to the corresponding places.

        :param timing_attributes: the special timing attributes to be distributed
        :param t_TRANSACT: the transition where the timestamps are computed
        :param activity: the activity
        """
        # only consider those that are required somewhere (i.e., have causal dependencies)
        timing_attribute: CPM_Attribute
        for attribute in timing_attributes:
            if not self.__causalModel.has_post_dependency(attribute):
                continue
            # distribute new last observations to global monitoring places
            global_lobs_place_name = get_attribute_global_last_observation_place_name(attribute.get_id())
            global_allobs_place_name = get_attribute_global_all_observations_place_name(attribute.get_id())
            if global_lobs_place_name in self.__controlFlowMap.cpn_places_by_name:
                # attribute is observed
                global_lobs_place = self.__controlFlowMap.cpn_places_by_name[global_lobs_place_name]
                self.__make_timing_lobs_logic(attribute, t_TRANSACT, activity, global_lobs_place)
            if global_allobs_place_name in self.__controlFlowMap.cpn_places_by_name:
                global_allobs_place = self.__controlFlowMap.cpn_places_by_name[global_allobs_place_name]
                self.__make_timing_allobs_logic(attribute, t_TRANSACT, activity, global_allobs_place)

    def __make_timing_lobs_logic(self, attribute: CPM_Attribute,
                                 t_TRANSACT: CPN_Transition,
                                 activity: CPM_Activity,
                                 global_lobs_place: CPN_Place):
        attribute_list_var = self.__colsetManager.get_one_var(
            get_attribute_list_colset_name(attribute.get_id())
        )
        attribute_domain_var = self.__colsetManager.get_one_var(
            get_attribute_domain_colset_name(attribute.get_id())
        )
        object_type_id_var = self.__colsetManager.get_one_var(
            get_object_type_ID_colset_name(activity.get_leading_type()))
        old_last_observation = "({0},{1})".format(
            object_type_id_var,
            attribute_list_var)
        new_last_observation = "({0},[{1}])".format(
            object_type_id_var,
            attribute_domain_var
        )
        lobs_old_arc = CPN_Arc(self.cpn_id_manager, global_lobs_place, t_TRANSACT, old_last_observation)
        lobs_new_arc = CPN_Arc(self.cpn_id_manager, t_TRANSACT, global_lobs_place, new_last_observation)
        self.__controlFlowMap.add_arc(lobs_old_arc)
        self.__controlFlowMap.add_arc(lobs_new_arc)
        if attribute.get_domain_type() is CPM_Domain_Type.EVENT_START_TIME:
            t_TRANSACT.add_start_time_output(attribute_domain_var)
        if attribute.get_domain_type() is CPM_Domain_Type.EVENT_COMPLETE_TIME:
            t_TRANSACT.add_complete_time_output(attribute_domain_var)

    def __make_timing_allobs_logic(self, attribute: CPM_Attribute,
                                   t_TRANSACT: CPN_Transition,
                                   activity: CPM_Activity,
                                   global_allobs_place: CPN_Place):
        attribute_domain_var = self.__colsetManager.get_one_var(
            get_attribute_domain_colset_name(attribute.get_id())
        )
        if attribute.get_domain_type() is CPM_Domain_Type.EVENT_START_TIME:
            t_TRANSACT.add_start_time_output(attribute_domain_var)
        if attribute.get_domain_type() is CPM_Domain_Type.EVENT_COMPLETE_TIME:
            t_TRANSACT.add_complete_time_output(attribute_domain_var)

    def __add_aggregation_logic_for_attribute(self, activity: CPM_Activity,
                                              attr_VALUATED: CPM_Attribute, attr_AGGREGATED: CPM_Attribute,
                                              t_CONTROL: CPN_Transition, t_VALUATE: CPN_Transition,
                                              sagg: AggregationSelection, fagg: AggregationFunction
                                              ):
        """
        1. make selection transition
        2. make aggregation transition
        3. connect to valuation transition

        :param attr_VALUATED: the attribute to be valuated
        :param attr_AGGREGATED: the attribute to be a aggregated
        :param t_CONTROL: the control transition of the activity
        :param t_VALUATE: the valuation transition of attr_VALUATED
        """
        # 1 Make selection transition:
        #   - initialize the transition
        #   - get the leading object ID from t_CONTROL
        #   - select the values from the global observation place
        p_SELECTIONS = \
            self.__add_aggregation_logic__selection(activity, attr_VALUATED, attr_AGGREGATED, t_CONTROL, t_VALUATE,
                                                    sagg)
        # 2. make aggregation transition
        # 3. connect to valuation transition
        p_AGGREGATED = \
            self.__add_aggregation_logic__aggregation(activity, attr_VALUATED, attr_AGGREGATED, t_VALUATE,
                                                      p_SELECTIONS, fagg)


    def __add_aggregation_logic__selection(self, activity: CPM_Activity,
                                           attr_VALUATED: CPM_Attribute, attr_AGGREGATED: CPM_Attribute,
                                           t_CONTROL: CPN_Transition, t_VALUATE: CPN_Transition,
                                           sagg: AggregationSelection
                                           ):
        x = float(t_VALUATE.x)
        y = float(t_VALUATE.y)
        y_p_SELECTED = str(y - 150)
        y_t_SELECT = str(y - 200)
        x_p_CONTROL_SELECTION = str(x - 100)
        y_p_CONTROL_SELECTION = str(y - 200)
        p_ALLOBS = self.__controlFlowMap.get_allobs_place(attr_AGGREGATED)
        leading_type = activity.get_leading_type()
        leading_type_colset_name = get_object_type_colset_name(leading_type)
        allobs_colset_name = get_attribute_all_observations_colset_name(attr_AGGREGATED.get_id())
        observations_list_colset_name = get_attribute_observations_list_colset_name(attr_AGGREGATED.get_id())
        leading_type_var = \
            self.__colsetManager.get_one_var(leading_type_colset_name)
        allobs_colset_var = \
            self.__colsetManager.get_one_var(allobs_colset_name)
        observations_list_var = \
            self.__colsetManager.get_one_var(observations_list_colset_name)
        # 1 Make selection transition: __add_aggregation_logic___selection
        #   - initialize the transition
        #   - get the leading object ID from t_CONTROL
        #   - select the values from the global observation place
        t_SELECT = self.__controlFlowMap.add_aggregation_selection_transition(
            CPN_Transition(transition_type=TransitionType.SILENT,
                           name=get_aggregation_selection_transition_name(attr_VALUATED, attr_AGGREGATED),
                           x=str(x), y=y_t_SELECT,
                           cpn_id_manager=self.cpn_id_manager,
                           activity=activity)
            , attr_VALUATED, attr_AGGREGATED)
        p_CONTROL_SELECTION = self.__controlFlowMap.add_place(
            CPN_Place(name=get_control_selection_place_name(attr_VALUATED, attr_AGGREGATED),
                      x=x_p_CONTROL_SELECTION, y=y_p_CONTROL_SELECTION,
                      cpn_id_manager=self.cpn_id_manager,
                      colset_name=leading_type_colset_name,
                      object_type=leading_type)
        )
        p_SELECTED = self.__controlFlowMap.add_place(
            CPN_Place(name=get_selected_values_place_name(attr_VALUATED, attr_AGGREGATED),
                      x=str(x), y=y_p_SELECTED,
                      cpn_id_manager=self.cpn_id_manager,
                      colset_name=observations_list_colset_name
                      )
        )
        self.__controlFlowMap.add_arc(
            CPN_Arc(self.cpn_id_manager, t_CONTROL, p_CONTROL_SELECTION, leading_type_var)
        )
        self.__controlFlowMap.add_arc(
            CPN_Arc(self.cpn_id_manager, p_CONTROL_SELECTION, t_SELECT, leading_type_var)
        )
        self.__controlFlowMap.add_arc(
            CPN_Arc(self.cpn_id_manager, p_ALLOBS, t_SELECT, allobs_colset_var)
        )
        self.__controlFlowMap.add_arc(
            CPN_Arc(self.cpn_id_manager, t_SELECT, p_ALLOBS, allobs_colset_var)
        )
        self.__controlFlowMap.add_arc(
            CPN_Arc(self.cpn_id_manager, t_SELECT, p_SELECTED, observations_list_var)
        )
        t_SELECT.add_guard_conjunct(
            "{0}={1}({2},{3},{4})".format(
                observations_list_var,
                sagg.get_function_name(),
                leading_type_var,
                get_now_time_getter_name() + "()",
                allobs_colset_var
            )
        )
        return p_SELECTED

    def __add_system_observation_logic_for_attribute(
            self, attribute: CPM_Attribute, activity: CPM_Activity, t_TRANSACT: CPN_Transition
    ):
        p_ALLOBS = self.__controlFlowMap.get_allobs_place(attribute)
        object_type_colset_name = get_object_type_colset_name(activity.get_leading_type())
        domain_observation_colset_name = get_attribute_domain_colset_name(attribute.get_id())
        all_observations_colset_name = get_attribute_all_observations_colset_name(attribute.get_id())
        object_type_var = self.__colsetManager.get_one_var(object_type_colset_name)
        domain_observation_var = self.__colsetManager.get_one_var(domain_observation_colset_name)
        all_observations_var = self.__colsetManager.get_one_var(all_observations_colset_name)
        self.__controlFlowMap.add_arc(
            CPN_Arc(self.cpn_id_manager, p_ALLOBS, t_TRANSACT, all_observations_var)
        )
        self.__controlFlowMap.add_arc(
            CPN_Arc(self.cpn_id_manager, t_TRANSACT, p_ALLOBS,
                    "({0},{1},{2})::{3}".format(
                        object_type_var,
                        get_now_time_getter_name() + "()",
                        domain_observation_var,
                        all_observations_var
                    ))
        )

    def __add_system_observation_logic_for_attributes(
            self, attributes: list[CPM_Attribute], activity: CPM_Activity, t_TRANSACT: CPN_Transition
    ):
        for attribute in attributes:
            if not self.__causalModel.has_post_dependency(attribute, aggregated=True):
                continue
            self.__add_system_observation_logic_for_attribute(attribute, activity, t_TRANSACT)

    def __add_aggregation_logic__aggregation(self, activity: CPM_Activity, attr_VALUATED: CPM_Attribute, attr_AGGREGATED: CPM_Attribute,
                                             t_VALUATE, p_SELECTIONS: CPN_Place, fagg: AggregationFunction):
        x = float(t_VALUATE.x)
        y = float(t_VALUATE.y)
        y_p_AGGREGATED = str(y - 50)
        y_t_AGGREGATE = str(y - 100)
        observations_list_colset_name = get_attribute_observations_list_colset_name(attr_AGGREGATED.get_id())
        observations_list_variable = self.__colsetManager.get_one_var(observations_list_colset_name)
        output_domain = fagg.output_domain
        output_domain_colset_name = get_domain_colset_name(output_domain)
        output_domain_variable = self.__colsetManager.get_one_var(output_domain_colset_name)
        t_AGGREGATE = self.__controlFlowMap.add_aggregation_transition(
            CPN_Transition(transition_type=TransitionType.SILENT,
                           name=get_aggregation_transition_name(attr_VALUATED, attr_AGGREGATED),
                           x=str(x), y=y_t_AGGREGATE,
                           cpn_id_manager=self.cpn_id_manager),
            attr_VALUATED, attr_AGGREGATED
        )
        p_AGGREGATED = self.__controlFlowMap.add_place(
            CPN_Place(name=get_aggregated_values_place_name(attr_VALUATED, attr_AGGREGATED),
                      x=str(x), y=y_p_AGGREGATED, cpn_id_manager=self.cpn_id_manager,
                      colset_name=output_domain_colset_name)
        )
        self.__controlFlowMap.add_arc(
            CPN_Arc(self.cpn_id_manager, p_SELECTIONS, t_AGGREGATE, observations_list_variable)
        )
        self.__controlFlowMap.add_arc(
            CPN_Arc(self.cpn_id_manager, t_AGGREGATE, p_AGGREGATED, output_domain_variable)
        )
        # TODO: make this safer - this does not work if the same output domain is used for multiple aggregations
        self.__controlFlowMap.add_arc(
            CPN_Arc(self.cpn_id_manager, p_AGGREGATED, t_VALUATE, output_domain_variable)
        )
        t_AGGREGATE.add_guard_conjunct(
            "{0}={1}({2})".format(
                output_domain_variable,
                fagg.get_function_name(),
                observations_list_variable
            )
        )

        return p_AGGREGATED
