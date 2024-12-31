from causal_model.causal_process_model import CausalProcessModel
from causal_model.causal_process_structure import CPM_Attribute, CPM_Activity
from process_model.petri_net import SimplePetriNet, SimplePetriNetPlace, SimplePetriNetTransition, SimplePetriNetArc
from simulation_model.colset import ColsetManager
from simulation_model.cpn_utils.cpn_arc import CPN_Arc
from simulation_model.cpn_utils.cpn_place import CPN_Place
from simulation_model.cpn_utils.cpn_transition import CPN_Transition, TransitionType
from simulation_model.cpn_utils.xml_utils.cpn_id_managment import CPN_ID_Manager
from simulation_model.io_action import get_activity_event_writer_name, get_activity_event_table_initializer_name


class ControlFlowMap:
    cpn_places: list[CPN_Place] = list()
    cpn_transitions: list[CPN_Transition] = list()
    cpn_nodes_by_id: dict = dict()
    cpn_places_by_id: dict = dict()
    cpn_places_by_name: dict[str, CPN_Place] = dict()
    cpn_places_by_simple_pn_place_id: dict = dict()
    cpn_transitions_by_simple_pn_transition_id: dict[str, CPN_Transition] = dict()
    cpn_transitions_by_id: dict = dict()
    cpn_arcs: list[CPN_Arc] = list()
    cpn_arcs_by_id: dict = dict()
    cpn_arcs_by_simple_pn_arc_id: dict = dict()

    def __init__(self):
        pass

    def add_place(self, place: CPN_Place, simple_place_id: str = None):
        place_id = place.get_id()
        place_name = place.get_name()
        if place_id in self.cpn_places_by_id or place_name in self.cpn_places_by_name:
            raise ValueError("Place already added")
        self.cpn_places_by_id[place_id] = place
        self.cpn_nodes_by_id[place_id] = place
        self.cpn_places_by_name[place_name] = place
        self.cpn_places.append(place)
        if simple_place_id is not None:
            self.cpn_places_by_simple_pn_place_id[simple_place_id] = place

    def add_transition(self, transition: CPN_Transition, simple_transition_id: str = None):
        transition_id = transition.get_id()
        if transition_id in self.cpn_transitions_by_id:
            raise ValueError("Transition already added")
        self.cpn_transitions_by_id[transition_id] = transition
        self.cpn_nodes_by_id[transition_id] = transition
        self.cpn_transitions.append(transition)
        if simple_transition_id is not None:
            self.cpn_transitions_by_simple_pn_transition_id[simple_transition_id] = transition

    def add_arc(self, arc: CPN_Arc, simple_pn_arc_id=None):
        arc_id = arc.get_id()
        if arc_id in self.cpn_arcs_by_id:
            raise ValueError("Arc already added")
        self.cpn_arcs_by_id[arc_id] = arc
        self.cpn_arcs.append(arc)
        if simple_pn_arc_id is not None:
            self.cpn_arcs_by_simple_pn_arc_id[simple_pn_arc_id] = arc

    def remove_arc(self, arc: CPN_Arc):
        a: CPN_Arc
        arc_id = arc.get_id()
        for p in self.cpn_places:
            p.incoming_arcs = list(filter(lambda a: (a.get_id() != arc_id), p.incoming_arcs))
            p.outgoing_arcs = list(filter(lambda a: (a.get_id() != arc_id), p.outgoing_arcs))
        for t in self.cpn_transitions:
            t.incoming_arcs = list(filter(lambda a: (a.get_id() != arc_id), t.incoming_arcs))
            t.outgoing_arcs = list(filter(lambda a: (a.get_id() != arc_id), t.outgoing_arcs))
        self.cpn_arcs = list(filter(lambda a: not (a.get_id() == arc_id), self.cpn_arcs))
        self.cpn_arcs_by_id = {key: value for key, value in self.cpn_arcs_by_id.items() if key != arc_id}
        self.cpn_arcs_by_simple_pn_arc_id = {
            key: value for key, value in self.cpn_arcs_by_simple_pn_arc_id.items() if value.get_id() != arc_id}


def get_attribute_place_name(attribute_id: str, suffix):
    return "p_" + "_".join(attribute_id.split(" ")) + "_" + suffix


def get_transition_attribute_place_name(transition_id: str, attribute_id: str, suffix):
    return "p_" + "_".join(transition_id.split(" ")) + "_" + "_".join(attribute_id.split(" ")) + "_" + suffix


def get_attribute_global_last_observation_place_name(attribute_id):
    """
    Canonical name of the unique place in the net where the last observation of some event
    attribute is being monitored.

    :param attribute_id: the attribute being monitored
    :return: the canonical name
    """
    return get_attribute_place_name(attribute_id, "LAST")


def get_preset_attribute_last_observation_place_name(transition_id, attribute_id):
    """
    Canonical name for places that hold the value of an attribute in the preset of
    the valuated attribute
    :param transition_id: the currently transformed transition of some activity
    :param attribute_id: the preset attribute of some attribute that is being valuated for the activity
    :return: the canonical name/identifier
    """
    return get_transition_attribute_place_name(transition_id, attribute_id, "LAST")


def get_attribute_valuation_main_in_place_name(transition_id, attribute_id):
    return get_transition_attribute_place_name(transition_id, attribute_id, "IN_MAIN")


def get_attribute_valuation_main_out_place_name(transition_id, attribute_id):
    return get_transition_attribute_place_name(transition_id, attribute_id, "OUT_MAIN")


def get_start_transition_id(t: SimplePetriNetTransition):
    return "t_start_" + t.get_id()


def get_attribute_valuation_transition_name(transition_id: str, attr_id: str):
    return "t_V_" + transition_id + "_" + attr_id


def get_control_place_id_case(t: SimplePetriNetTransition):
    return "p_control_case_" + t.get_id()


def get_control_place_id_event(t: SimplePetriNetTransition):
    return "p_control_event_" + t.get_id()


def get_global_semaphore_place_name():
    return "p_global_semaphore"


class ControlFlowManager:
    # some coordinates to put nodes somewhere
    # TODO: use some graph layouting algorithm
    running_x = 0
    running_y = -100

    def __init__(self,
                 cpn_id_manager: CPN_ID_Manager,
                 petriNet: SimplePetriNet,
                 causalModel: CausalProcessModel,
                 colsetManager: ColsetManager,
                 initial_marking_case_ids: list[str]
                 ):
        self.cpn_id_manager = cpn_id_manager
        self.__petriNet = petriNet
        self.__causalModel = causalModel
        self.__colsetManager = colsetManager
        self.__controlFlowMap = ControlFlowMap()
        self.initial_marking_case_ids = initial_marking_case_ids
        # remember the variable names in the event attribute value maps
        self.__eaval_parameter_tuples = {}

    def merge_models(self):
        self.cast_petri_net()
        self.merge_causal_model()

    def cast_petri_net(self):
        """
        Wrap the Petri net into a CPN.
        """
        places = self.__petriNet.get_places()
        transitions = self.__petriNet.get_transitions()
        arcs = self.__petriNet.get_arcs()
        place: SimplePetriNetPlace
        transition: SimplePetriNetTransition
        arc: SimplePetriNetArc
        v_case_id = self.__colsetManager.get_one_var(
            self.__colsetManager.get_case_id_colset().colset_name
        )
        for arc in arcs:
            place = arc.get_place()
            transition = arc.get_transition()
            cpn_place = self.__convert_simple_pn_place(place)
            cpn_transition = self.__convert_simple_pn_transition(transition)
            arc_direction = arc.get_direction()
            source = cpn_place if arc_direction == "PtoT" else cpn_transition
            target = cpn_transition if arc_direction == "PtoT" else cpn_place
            cpn_arc = CPN_Arc(self.cpn_id_manager, source, target, v_case_id)
            self.__controlFlowMap.add_arc(cpn_arc, arc.get_id())
        if not all(p.get_id() in self.__controlFlowMap.cpn_places_by_simple_pn_place_id
                   for p in places):
            raise ValueError("Unconnected place found in the Petri net.")
        if not all(t.get_id() in self.__controlFlowMap.cpn_transitions_by_simple_pn_transition_id
                   for t in transitions):
            raise ValueError("Unconnected transition found in the Petri net.")

    def __convert_simple_pn_place(self, simple_pn_place: SimplePetriNetPlace):
        simple_pn_place_id = simple_pn_place.get_id()
        if simple_pn_place_id in self.__controlFlowMap.cpn_places_by_simple_pn_place_id:
            return self.__controlFlowMap.cpn_places_by_simple_pn_place_id[simple_pn_place_id]
        colset_name = self.__colsetManager.get_case_id_colset().colset_name
        is_initial = simple_pn_place.is_initial
        timed_initial_marking = ['"{0}"@{1}'.format(t[0], t[1])
                                 for t in self.initial_marking_case_ids]
        initmark = "[" + ",".join(timed_initial_marking) + "]" if is_initial else None
        cpn_place = CPN_Place(name=simple_pn_place_id,
                              x=simple_pn_place.x,
                              y=simple_pn_place.y,
                              cpn_id_manager=self.cpn_id_manager,
                              colset_name=colset_name,
                              is_initial=is_initial,
                              initmark=initmark)
        self.__controlFlowMap.add_place(cpn_place, simple_pn_place_id)
        return cpn_place

    def __convert_simple_pn_transition(self, simple_pn_transition: SimplePetriNetTransition):
        simple_pn_transition_id = simple_pn_transition.get_id()
        if simple_pn_transition_id in self.__controlFlowMap.cpn_transitions_by_simple_pn_transition_id:
            return self.__controlFlowMap.cpn_transitions_by_simple_pn_transition_id[simple_pn_transition_id]
        labeling_function = self.__petriNet.get_labels()
        labeled_transition_ids = labeling_function.get_keys()
        is_labeled = simple_pn_transition_id in labeled_transition_ids
        transition_type = TransitionType.ACTIVITY if is_labeled else TransitionType.SILENT
        label = None if not is_labeled else labeling_function.get_label(simple_pn_transition_id)
        cpn_transition = CPN_Transition(transition_type, label,
                                        simple_pn_transition.x, simple_pn_transition.y,
                                        self.cpn_id_manager)
        self.__controlFlowMap.add_transition(cpn_transition, simple_pn_transition_id)
        return cpn_transition

    def get_cpn_places(self):
        return self.__controlFlowMap.cpn_places

    def get_cpn_transitions(self):
        return self.__controlFlowMap.cpn_transitions

    def get_cpn_arcs(self):
        return self.__controlFlowMap.cpn_arcs

    def merge_causal_model(self):
        self.__make_causal_places()
        # place to make activity executions atomic (a critical section)
        x, y = self.__get_node_coordinates(location=2)
        semaphore_place = CPN_Place(
            get_global_semaphore_place_name(), x, y, self.cpn_id_manager,
            colset_name= "INT",
            initmark="1"
        )
        self.__controlFlowMap.add_place(semaphore_place)
        cm_activities = self.__causalModel.get_activities()
        for act in cm_activities:
            act_name = act.get_name()
            act_transitions = self.__petriNet.get_transitions_with_label(act_name)
            t: SimplePetriNetTransition
            for t in act_transitions:
                self.__convert_transition(t, act)

    def __make_causal_places(self):
        non_agg_attributes = self.__causalModel.get_attributes_with_non_aggregated_dependencies()
        for attribute in non_agg_attributes:
            self.__make_last_observation_place(attribute)
        # TODO: aggregation logic

    def __make_last_observation_place(self, attribute: CPM_Attribute):
        """
        Make the unique place in the net where the last observation of some event
        attribute is being monitored.

        :param attribute: the attribute being monitored
        """
        lobs_place_name = get_attribute_global_last_observation_place_name(attribute.get_id())
        lobs_colset_name = self.__colsetManager.get_attribute_last_observation_colset_name(
            attribute.get_id()
        )
        x, y = self.__get_node_coordinates()
        # Initial marking should be an empty list (i.e., no observation) for all cases to be simulated
        initial_case_ids = [case_id for case_id, time in self.initial_marking_case_ids]
        initmark = "[" + ",".join(['("{0}",[])'.format(cid) for cid in initial_case_ids]) + "]"
        lobs_place = CPN_Place(lobs_place_name, x, y, self.cpn_id_manager, lobs_colset_name, False, initmark)
        self.__controlFlowMap.add_place(lobs_place)

    def __convert_transition(self, t: SimplePetriNetTransition, activity: CPM_Activity):
        start_t = self.__make_start_transition(t)
        control_p_case, control_p_event = self.__make_control_places(t)
        cpn_t = self.__controlFlowMap.cpn_transitions_by_simple_pn_transition_id[t.get_id()]
        caseid_var = self.__colsetManager.get_one_var(self.__colsetManager.get_case_id_colset().colset_name)
        int_var = self.__colsetManager.get_one_var("INT")
        control_a1 = CPN_Arc(self.cpn_id_manager, start_t, control_p_case, caseid_var)
        control_a2 = CPN_Arc(self.cpn_id_manager, control_p_case, cpn_t, caseid_var)
        self.__controlFlowMap.add_arc(control_a1)
        self.__controlFlowMap.add_arc(control_a2)
        control_b1 = CPN_Arc(self.cpn_id_manager, start_t, control_p_event, int_var)
        control_b2 = CPN_Arc(self.cpn_id_manager, control_p_event, cpn_t, int_var)
        self.__controlFlowMap.add_arc(control_b1)
        self.__controlFlowMap.add_arc(control_b2)
        self.__add_attribute_logic(t, start_t, cpn_t, activity)
        # Semaphore also carries a running event id
        sem = self.__controlFlowMap.cpn_places_by_name[get_global_semaphore_place_name()]
        sem_in  = CPN_Arc(self.cpn_id_manager, sem, start_t, str(int_var))
        sem_out = CPN_Arc(self.cpn_id_manager, cpn_t, sem, str(int_var) + " + 1")
        self.__controlFlowMap.add_arc(sem_in)
        self.__controlFlowMap.add_arc(sem_out)

    def __make_start_transition(self, t: SimplePetriNetTransition) -> CPN_Transition:
        start_t_name = get_start_transition_id(t)
        x = t.x - 50
        y = t.y
        start_t = CPN_Transition(TransitionType.SILENT, start_t_name, x, y, self.cpn_id_manager, "")
        self.__controlFlowMap.add_transition(start_t)
        # remove in-arcs from original transition
        # make them in-arcs of new start transition
        in_arcs = self.__petriNet.get_incoming_arcs(t.get_id())
        cpn_in_arcs = [self.__controlFlowMap.cpn_arcs_by_simple_pn_arc_id[arc.get_id()] for arc in in_arcs]
        arc: CPN_Arc
        for arc in cpn_in_arcs:
            self.__controlFlowMap.remove_arc(arc)
            new_arc = CPN_Arc(self.cpn_id_manager, arc.source, start_t, arc.annotation_text)
            self.__controlFlowMap.add_arc(new_arc)
        return start_t

    def __make_control_places(self, t: SimplePetriNetTransition) -> [CPN_Place, CPN_Place]:
        control_p_name_case = get_control_place_id_case(t)
        control_p_name_event = get_control_place_id_event(t)
        x = t.x + 50
        y = t.y
        control_p_case = CPN_Place(control_p_name_case, x, y, self.cpn_id_manager,
                              self.__colsetManager.get_case_id_colset().colset_name)
        control_p_event = CPN_Place(control_p_name_event, x, y, self.cpn_id_manager, "INT")
        self.__controlFlowMap.add_place(control_p_case)
        self.__controlFlowMap.add_place(control_p_event)
        return control_p_case, control_p_event

    def __get_node_coordinates(self, location=1):
        x = self.running_x
        y = self.running_y * location
        self.running_x = self.running_x + 50
        return x, y

    def __add_attribute_logic(self, simple_labeled_t: SimplePetriNetTransition, cpn_start_t: CPN_Transition,
                              cpn_labeled_t: CPN_Transition, activity: CPM_Activity):
        # for each activity attribute, make a transition to valuate the attribute,
        # and feed it into the labeled transition
        # add connections w.r.t non-aggregated dependencies
        # TODO: add connections w.r.t aggregated dependencies
        attribute_ids = self.__causalModel.get_attribute_ids_by_activity_id(activity.get_id())
        transition_id = simple_labeled_t.get_id()
        # for each preset attribute, that is, each attribute on which some event attribute at the current
        # activity depends, we check whether a last observation exists (to guard the start transition of the
        # activity), and if it does exist, we query the last observation to be used during valuation.
        self.__current_transformed_transition_dependent_attributes = set()
        for i, attribute_id in enumerate(attribute_ids):
            self.__collect_preset_attributes(attribute_id)
        self.__control_transition_for_last_observations(cpn_start_t)
        # As we now iterate the event attributes to build control structures, we get the last observations
        # from the start transition guard.
        attribute_domain_vars = []
        attribute_list_vars = []
        for i, attribute_id in enumerate(attribute_ids):
            x = simple_labeled_t.x + 50.0
            y = simple_labeled_t.y + 50.0 * (i + 1)
            valuated_attribute_place = self.__make_attribute_valuation_structure(
                transition_id, cpn_start_t, attribute_id, x, y)
            attribute_domain_var = self.__colsetManager.get_one_var(
                self.__colsetManager.get_attribute_domain_colset_name(attribute_id)
            )
            attribute_domain_vars.append(attribute_domain_var)
            global_lobs_place_name = get_attribute_global_last_observation_place_name(attribute_id)
            if global_lobs_place_name in self.__controlFlowMap.cpn_places_by_name:
                # attribute is observed (there are post-dependencies)
                # get two variables: the another variable for the old last observation
                attribute_list_var = self.__colsetManager.get_one_var(
                    self.__colsetManager.get_attribute_list_colset_name(attribute_id)
                )
                attribute_list_vars.append(attribute_list_var)
            attribute_to_event = CPN_Arc(self.cpn_id_manager, valuated_attribute_place, cpn_labeled_t,
                                         attribute_domain_var)
            self.__controlFlowMap.add_arc(attribute_to_event)
        eaval_var = self.__colsetManager.get_one_var(
            self.__colsetManager.get_activity_eaval_colset_name(activity.get_id())
        )
        case_id_var = self.__colsetManager.get_one_var(
            self.__colsetManager.get_case_id_colset().colset_name
        )
        self.__eaval_parameter_tuples[activity.get_name()] = [case_id_var] + attribute_domain_vars
        act_guard = "{0}=({1},{2})".format(
            eaval_var,
            case_id_var,
            ",".join(attribute_domain_vars)
        )
        cpn_labeled_t.add_conjunct(act_guard)
        # distribute new last observations to global monitoring places
        for i, attribute_id in enumerate(attribute_ids):
            global_lobs_place_name = get_attribute_global_last_observation_place_name(attribute_id)
            if global_lobs_place_name not in self.__controlFlowMap.cpn_places_by_name:
                # attribute is not observed (no post-dependencies)
                continue
            attribute_list_var_old   = attribute_list_vars[i]
            attribute_domain_var_new = attribute_domain_vars[i]
            global_lobs_place = self.__controlFlowMap.cpn_places_by_name[
                global_lobs_place_name
            ]
            old_last_observation = "({0},{1})".format(
                case_id_var,
                attribute_list_var_old
            )
            new_last_observation = "({0},[{1}])".format(
                case_id_var,
                attribute_domain_var_new
            )
            lobs_old_arc = CPN_Arc(self.cpn_id_manager, global_lobs_place, cpn_labeled_t, old_last_observation)
            lobs_new_arc = CPN_Arc(self.cpn_id_manager, cpn_labeled_t, global_lobs_place, new_last_observation)
            self.__controlFlowMap.add_arc(lobs_old_arc)
            self.__controlFlowMap.add_arc(lobs_new_arc)

    def __make_attribute_valuation_structure(self, transition_id: str,
                                             start_transition: CPN_Transition, attribute_id: str, x=0.0, y=0.0) \
            -> CPN_Place:
        """
        For the activity of this transition, valuate one event attribute
        w.r.t the dependencies specified in the causal model.

        :param transition_id: Some identifier of this section (transition)
        :param start_transition: The start transition of the activity section
        :param attribute_id: The ID of the attribute
        :param x: x-coordinate of transition in visual net
        :param y: y-coordinate of transition in visual net
        :returns The CPN_Place that will carry the valuation result
        """
        # make valuation transition and its guard
        preset = self.__causalModel.get_preset(attribute_id)
        preset_attr_ids = [in_relation.get_in().get_id() for in_relation in preset]
        preset_domain_colset_names = [
            self.__colsetManager.get_attribute_domain_colset_name(preset_attr_id)
            for preset_attr_id in preset_attr_ids]
        preset_domain_variables = [
            self.__colsetManager.get_one_var(preset_colset_name)
            for preset_colset_name in preset_domain_colset_names
        ]
        attr_colset_name = self.__colsetManager.get_attribute_domain_colset_name(attribute_id)
        attr_variable = self.__colsetManager.get_one_var(attr_colset_name)
        valuation_transition_name = get_attribute_valuation_transition_name(transition_id, attribute_id)
        valuation_call = self.__causalModel.get_attribute_valuations(). \
            get_attribute_valuation(attribute_id).get_call()
        valuation_guard = "[" + attr_variable + "=" + valuation_call(preset_domain_variables) + "]"
        valuation_transition = CPN_Transition(TransitionType.SILENT, valuation_transition_name, x, y,
                                              self.cpn_id_manager,
                                              valuation_guard)
        self.__controlFlowMap.add_transition(valuation_transition)
        # Add control place to preset (colset: UNIT) so that valuation happens only once
        main_control_place = CPN_Place(
            get_attribute_valuation_main_in_place_name(transition_id, attribute_id), x - 50, y, self.cpn_id_manager)
        main_control_arc1 = CPN_Arc(self.cpn_id_manager, start_transition, main_control_place)
        main_control_arc2 = CPN_Arc(self.cpn_id_manager, main_control_place, valuation_transition)
        self.__controlFlowMap.add_place(main_control_place)
        self.__controlFlowMap.add_arc(main_control_arc1)
        self.__controlFlowMap.add_arc(main_control_arc2)
        # connect dependencies: for each attribute, the last-observation-place with the start transition
        # add conjunct to the start transition guard (last observation need to be well-defined)
        # note that this can be redundant with other attributes at this transition
        # add place of preset attribute domain and connect it with valuation transition.
        for i, in_relation in enumerate(preset):
            if in_relation.is_aggregated():
                raise NotImplementedError()
            # else:
            in_attr_id = in_relation.get_in().get_id()
            in_attr_colset_name = self.__colsetManager.get_attribute_domain_colset_name(in_attr_id)
            in_attr_place_name = get_preset_attribute_last_observation_place_name(transition_id, in_attr_id)
            in_attr_variable = self.__colsetManager.get_one_var(in_attr_colset_name)
            lobs_colset_name = self.__colsetManager.get_attribute_last_observation_colset_name(in_attr_id)
            lobs_place = CPN_Place(in_attr_place_name, x + 50, y - 50 * i, self.cpn_id_manager,
                                   in_attr_colset_name)
            self.__controlFlowMap.add_place(lobs_place)
            lobs_variable = self.__colsetManager.get_one_var(lobs_colset_name)
            # the expression to get the last observation: the head (hd) of the second element (#2)
            # the last_observation colset is a product colset and the second element is a list
            # carrying either the last observation or nothing
            lobs_expression = "hd(#2 {0})".format(lobs_variable)
            start_to_lobs = CPN_Arc(self.cpn_id_manager, start_transition, lobs_place, lobs_expression)
            lobs_to_vt = CPN_Arc(self.cpn_id_manager, lobs_place, valuation_transition, in_attr_variable)
            self.__controlFlowMap.add_arc(start_to_lobs)
            self.__controlFlowMap.add_arc(lobs_to_vt)
        attr_domain_colset_name = self.__colsetManager.get_attribute_domain_colset_name(attribute_id)
        main_out_place = CPN_Place(
            get_attribute_valuation_main_out_place_name(transition_id, attribute_id), x + 50, y, self.cpn_id_manager,
            colset_name=attr_domain_colset_name)
        attr_domain_var = self.__colsetManager.get_one_var(attr_domain_colset_name)
        vt_to_mop = CPN_Arc(self.cpn_id_manager, valuation_transition, main_out_place, attr_domain_var)
        self.__controlFlowMap.add_place(main_out_place)
        self.__controlFlowMap.add_arc(vt_to_mop)
        return main_out_place

    def __collect_preset_attributes(self, attribute_id: str):
        preset = self.__causalModel.get_preset(attribute_id)
        preset_attr_ids = [in_relation.get_in().get_id() for in_relation in preset]
        for preset_attr_id in preset_attr_ids:
            self.__current_transformed_transition_dependent_attributes.add(preset_attr_id)

    def __control_transition_for_last_observations(self, start_transition: CPN_Transition):
        all_preset_attr_ids = list(self.__current_transformed_transition_dependent_attributes)
        all_preset_colset_names = [
            self.__colsetManager.get_attribute_last_observation_colset_name(preset_attr_id)
            for preset_attr_id in all_preset_attr_ids]
        all_preset_lobs_variables = [
            self.__colsetManager.get_one_var(preset_colset_name)
            for preset_colset_name in all_preset_colset_names
        ]
        # for each preset attribute of some event attribute, ...
        for i in range(len(all_preset_attr_ids)):
            preset_attr_id = all_preset_attr_ids[i]
            preset_lobs_variable = all_preset_lobs_variables[i]
            # ...make back and forth arcs of the last observation place with the start transition
            global_lobs_place_name = get_attribute_global_last_observation_place_name(preset_attr_id)
            global_lobs_place = self.__controlFlowMap.cpn_places_by_name[global_lobs_place_name]
            p_to_t = CPN_Arc(self.cpn_id_manager, global_lobs_place, start_transition, preset_lobs_variable)
            t_to_p = CPN_Arc(self.cpn_id_manager, start_transition, global_lobs_place, preset_lobs_variable)
            self.__controlFlowMap.add_arc(p_to_t)
            self.__controlFlowMap.add_arc(t_to_p)
            # ... make sure the activity can only be executed if there is a well-defined last observation
            # of the preset attribute.
            start_transition.add_conjunct("length(#2 {0})>0".format(preset_lobs_variable))

    def add_iostream(self):
        '''
        input (order);
        output ();
        action
        (write_place_order(order));
        '''
        cm_activities = self.__causalModel.get_activities()
        for act in cm_activities:
            act_name = act.get_name()
            act_id = act.get_id()
            act_transitions = self.__petriNet.get_transitions_with_label(act_name)
            t: SimplePetriNetTransition
            for t in act_transitions:
                # Example code layout:
                '''
                input(v_eid, v_register_patient_eaval);
                output();
                action(write_event_register_patient(v_eid, v_register_patient_eaval));
                '''
                cpn_t = self.__controlFlowMap.cpn_transitions_by_simple_pn_transition_id[t.get_id()]
                int_var = self.__colsetManager.get_one_var("INT")
                eaval_var = self.__colsetManager.get_one_var(
                    self.__colsetManager.get_activity_eaval_colset_name(act.get_id())
                )
                action_input  = int_var + "," + eaval_var
                action_output = ""
                action_parameters = '{0},"{1}",{2}'.format(
                    int_var,
                    act_name,
                    eaval_var
                )
                action = "{0}({1})".format(
                    get_activity_event_writer_name(act_id),
                    action_parameters
                )
                cpn_t.make_code(action_input, action_output, action)

    def get_kickstart_transition_name(self):
        return "t_kickstart"

    def get_kickstart_place_name(self):
        return "p_kickstart"

    def add_table_initializing(self):
        kickstart_transition = CPN_Transition(
            transition_type=TransitionType.SILENT,
            name=self.get_kickstart_transition_name(),
            x = -150,
            y = 0,
            cpn_id_manager=self.cpn_id_manager,
            priority="P_HIGH"
        )
        code_text = "input();output();action("
        act: CPM_Activity
        for act in self.__causalModel.get_activities():
            code_text += get_activity_event_table_initializer_name(act.get_id())
            code_text += "();"
        code_text = code_text[:-1] + ")"
        kickstart_transition.set_code(code_text)
        kickstart_place = CPN_Place(
            name=self.get_kickstart_place_name(),
            x = -200,
            y=0,
            cpn_id_manager=self.cpn_id_manager,
            initmark="()"
        )
        kickstart_arc = CPN_Arc(cpn_id_manager=self.cpn_id_manager,
                                source=kickstart_place,
                                target=kickstart_transition)
        self.__controlFlowMap.add_transition(kickstart_transition)
        self.__controlFlowMap.add_place(kickstart_place)
        self.__controlFlowMap.add_arc(kickstart_arc)

