import random

from causal_model.causal_process_model import CausalProcessModel
from causal_model.causal_process_structure import CPM_Attribute, CPM_Activity
from object_centric.object_centric_functions import get_sorted_object_insert_function_name, \
    get_completeness_by_relations_function_name, get_extract_object_type_by_ids_function_name
from object_centric.object_centric_petri_net import ObjectCentricPetriNet as OCPN, ObjectCentricPetriNetArc as Arc, \
    ObjectCentricPetriNetPlace as Place, ObjectCentricPetriNetTransition as Transition
from object_centric.object_centricity_management import ObjectCentricityManager
from object_centric.object_type_structure import ObjectType
from process_model.petri_net import ArcDirection
from simulation_model.colset import ColsetManager, Colset
from simulation_model.cpn_utils.cpn_arc import CPN_Arc
from simulation_model.cpn_utils.cpn_place import CPN_Place
from simulation_model.cpn_utils.cpn_transition import CPN_Transition, TransitionType
from simulation_model.cpn_utils.xml_utils.cpn_id_managment import CPN_ID_Manager
from simulation_model.functions import get_activity_event_writer_name, get_activity_event_table_initializer_name, \
    get_normalized_delay_from_now_function_name, get_list_diff_function_name
from simulation_model.simulation_parameters import SimulationParameters
from simulation_model.timing import ProcessTimeCategory


class ControlFlowMap:

    def __init__(self):
        self.cpn_places: list[CPN_Place] = list()
        self.cpn_lobs_places: list[CPN_Place] = list()
        self.cpn_transitions: list[CPN_Transition] = list()
        self.cpn_nodes_by_id: dict = dict()
        self.cpn_places_by_id: dict = dict()
        self.cpn_places_by_name: dict[str, CPN_Place] = dict()
        self.cpn_places_by_simple_pn_place_id: dict = dict()
        self.cpn_transitions_by_simple_pn_transition_id: dict[str, CPN_Transition] = dict()
        self.cpn_transitions_by_id: dict = dict()
        self.cpn_arcs: list[CPN_Arc] = list()
        self.cpn_arcs_by_id: dict = dict()
        self.cpn_arcs_by_simple_pn_arc_id: dict = dict()
        self.cpn_arcs_by_simple_pn_arc: dict = dict()
        self.split_transitions_in_to_out: dict[CPN_Transition, CPN_Transition] = dict()
        self.split_transitions_out_to_in: dict[CPN_Transition, CPN_Transition] = dict()
        self.split_transition_pairs_variable_types: dict[tuple[CPN_Transition, CPN_Transition], set[ObjectType]] = dict()

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

    def add_lobs_place(self, lobs_place):
        self.add_place(lobs_place)
        self.cpn_lobs_places.append(lobs_place)

    def get_multi_object_type_transitions(self):
        arcs_by_transitions = {
            ct: list(filter(lambda a: a.source == ct or a.target == ct, self.cpn_arcs))
            for ct in self.cpn_transitions
        }
        transition_object_types_counts = {
            ct: len(set(filter(lambda ot: ot is not None, set([a.get_object_type() for a in ct_arcs]))))
            for ct, ct_arcs in arcs_by_transitions.items()
        }
        multi_object_type_transitions = [t for t, cnt in transition_object_types_counts.items() if cnt > 1]
        return multi_object_type_transitions

    def get_mapped_variable_arcs(self):
        mapped_arcs = list(filter(lambda a: a.ocpn_arc is not None, self.cpn_arcs))
        variable_arcs = list(filter(lambda a: a.ocpn_arc.is_variable(), mapped_arcs))
        return variable_arcs

    def get_place_to_transition_variable_arcs(self):
        variable_arcs = self.get_mapped_variable_arcs()
        p_to_t_arcs = list(filter(lambda a: a.orientation is ArcDirection.P2T, variable_arcs))
        return p_to_t_arcs

    def get_transition_to_place_variable_arcs(self):
        variable_arcs = self.get_mapped_variable_arcs()
        t_to_p_arcs = list(filter(lambda a: a.orientation is ArcDirection.T2P, variable_arcs))
        return t_to_p_arcs

    def add_split_transition_pair(self, start_t: CPN_Transition, end_t: CPN_Transition):
        self.split_transitions_in_to_out[start_t] = end_t
        self.split_transitions_out_to_in[end_t] = start_t
        self.split_transition_pairs_variable_types[start_t, end_t] = set()

    def is_split_in_transition(self, transition: CPN_Transition):
        return transition in self.split_transitions_in_to_out

    def is_split_out_transition(self, transition: CPN_Transition):
        return transition in self.split_transitions_out_to_in

    def get_split_out_for_split_in(self, split_in_transition: CPN_Transition):
        return self.split_transitions_in_to_out[split_in_transition]

    def get_split_in_for_split_out(self, split_out_transition: CPN_Transition):
        return self.split_transitions_out_to_in[split_out_transition]

    def get_split_transition_pairs_variable_types(self):
        return self.split_transition_pairs_variable_types

    def add_split_transition_pair_variable_type(self, split_in: CPN_Transition, split_out: CPN_Transition, ot: ObjectType):
        self.split_transition_pairs_variable_types[(split_in, split_out)].add(ot)


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


def get_start_transition_id(t: Transition):
    return "t_start_" + t.get_id()


def get_attribute_valuation_transition_name(transition_id: str, attr_id: str):
    return "t_V_" + transition_id + "_" + attr_id


def get_control_place_id_case(t: Transition):
    return "p_control_case_" + t.get_id()


def get_control_place_id_event(t: Transition):
    return "p_control_event_" + t.get_id()


def get_global_semaphore_place_name():
    return "p_global_semaphore"


def get_kickstart_transition_name():
    return "t_kickstart"


def get_kickstart_place_name():
    return "p_kickstart"


class ControlFlowManager:
    # some coordinates to put nodes somewhere
    # TODO: use some graph layouting algorithm
    running_x = 0
    running_y = -100

    def __init__(self,
                 cpn_id_manager: CPN_ID_Manager,
                 petriNet: OCPN,
                 causalModel: CausalProcessModel,
                 simulationParameters: SimulationParameters,
                 objectCentricityManager: ObjectCentricityManager,
                 colsetManager: ColsetManager
                 ):
        self.cpn_id_manager = cpn_id_manager
        self.__petriNet = petriNet
        self.__causalModel = causalModel
        self.__simulationParameters = simulationParameters
        self.__objectCentricityManager = objectCentricityManager
        self.__colsetManager = colsetManager
        self.__controlFlowMap = ControlFlowMap()
        # remember the variable names in the event attribute value maps
        self.__eaval_parameter_tuples = {}
        self.__synchronized_transitions = {}

    def merge_models(self):
        self.parse_object_type_net_info()
        self.cast_petri_net()
        self.merge_causal_model()

    def parse_object_type_net_info(self):
        self.__objectCentricityManager.parse_object_type_net_info()

    def cast_petri_net(self):
        """
        Wrap the Petri net into a CPN.
        """
        places = self.__petriNet.get_places()
        transitions = self.__petriNet.get_transitions()
        arcs = self.__petriNet.get_arcs()
        place: Place
        transition: Transition
        arc: Arc
        for arc in arcs:
            place = arc.get_place()
            transition = arc.get_transition()
            place_type = place.get_object_type()
            v_object_type = self.__colsetManager.get_one_var(
                self.__colsetManager.get_object_type_colset_name(place_type)
            )
            cpn_place = self.__convert_simple_pn_place(place)
            cpn_transition = self.__convert_simple_pn_transition(transition)
            arc_direction = arc.get_direction()
            source = cpn_place if arc_direction == ArcDirection.P2T else cpn_transition
            target = cpn_transition if arc_direction == ArcDirection.P2T else cpn_place
            cpn_arc = CPN_Arc(self.cpn_id_manager, source, target, v_object_type, ocpn_arc=arc)
            self.__controlFlowMap.add_arc(cpn_arc, arc.get_id())
        if not all(p.get_id() in self.__controlFlowMap.cpn_places_by_simple_pn_place_id
                   for p in places):
            raise ValueError("Unconnected place found in the Petri net.")
        if not all(t.get_id() in self.__controlFlowMap.cpn_transitions_by_simple_pn_transition_id
                   for t in transitions):
            raise ValueError("Unconnected transition found in the Petri net.")

    def __convert_simple_pn_place(self, simple_pn_place: Place):
        simple_pn_place_id = simple_pn_place.get_id()
        if simple_pn_place_id in self.__controlFlowMap.cpn_places_by_simple_pn_place_id:
            return self.__controlFlowMap.cpn_places_by_simple_pn_place_id[simple_pn_place_id]
        place_type = simple_pn_place.get_object_type()
        colset_name = self.__colsetManager.get_object_type_colset_name(place_type)
        initmark = None
        ################# TODO Testcode Testcode Testcode ########################
        if colset_name == "C_orders" and simple_pn_place.is_initial:
            initmark = '[("o1", 3, ["i1", "i2"]) @ 1]'
        if colset_name == "C_items" and simple_pn_place.is_initial:
            initmark = '[("i1", 3, "o1")@1,("i2", 3, "o1")@1, ("i3", 2, "o2")@0]'
        #########################################################################
        cpn_place = CPN_Place(name=simple_pn_place_id,
                              x=simple_pn_place.x,
                              y=simple_pn_place.y,
                              cpn_id_manager=self.cpn_id_manager,
                              colset_name=colset_name,
                              is_initial=False,
                              initmark=initmark,
                              ocpn_place=simple_pn_place)
        self.__controlFlowMap.add_place(cpn_place, simple_pn_place_id)
        return cpn_place

    def __convert_simple_pn_transition(self, simple_pn_transition: Transition):
        simple_pn_transition_id = simple_pn_transition.get_id()
        if simple_pn_transition_id in self.__controlFlowMap.cpn_transitions_by_simple_pn_transition_id:
            return self.__controlFlowMap.cpn_transitions_by_simple_pn_transition_id[simple_pn_transition_id]
        labeling_function = self.__petriNet.get_labels()
        labeled_transition_ids = labeling_function.get_keys()
        is_labeled = simple_pn_transition_id in labeled_transition_ids
        transition_type = TransitionType.ACTIVITY if is_labeled else TransitionType.SILENT
        label = simple_pn_transition_id if not is_labeled else labeling_function.get_label(simple_pn_transition_id)
        cpn_transition = CPN_Transition(transition_type, label,
                                        simple_pn_transition.x + 300, simple_pn_transition.y,
                                        self.cpn_id_manager, ocpn_transition=simple_pn_transition)
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
        object_type = self.__causalModel.get_activity_for_attribute_id(attribute.get_id()).get_leading_type()
        lobs_place = CPN_Place(lobs_place_name, x, y, self.cpn_id_manager, lobs_colset_name, False,
                               object_type=object_type)
        self.__controlFlowMap.add_lobs_place(lobs_place)

    def __convert_activity_transition(self, t: Transition, activity: CPM_Activity):
        start_t = self.__make_start_transition(t)
        end_t = self.__controlFlowMap.cpn_transitions_by_simple_pn_transition_id[t.get_id()]
        self.__controlFlowMap.add_split_transition_pair(start_t, end_t)
        control_p_case, control_p_event = self.__make_control_places(t)
        leading_type = t.get_leading_type()
        leading_type_var = self.__colsetManager.get_one_var(
            self.__colsetManager.get_object_type_colset_name(leading_type))
        int_var = self.__colsetManager.get_one_var("INT")
        control_a1 = CPN_Arc(self.cpn_id_manager, start_t, control_p_case, leading_type_var)
        control_a2 = CPN_Arc(self.cpn_id_manager, control_p_case, end_t, leading_type_var)
        self.__controlFlowMap.add_arc(control_a1)
        self.__controlFlowMap.add_arc(control_a2)
        control_b1 = CPN_Arc(self.cpn_id_manager, start_t, control_p_event, int_var)
        control_b2 = CPN_Arc(self.cpn_id_manager, control_p_event, end_t, int_var)
        self.__controlFlowMap.add_arc(control_b1)
        self.__controlFlowMap.add_arc(control_b2)
        self.__add_attribute_logic(t, start_t, end_t, activity)
        # Semaphore also carries a running event id
        sem = self.__controlFlowMap.cpn_places_by_name[get_global_semaphore_place_name()]
        sem_in = CPN_Arc(self.cpn_id_manager, sem, start_t, str(int_var))
        sem_out = CPN_Arc(self.cpn_id_manager, end_t, sem, str(int_var) + " + 1")
        self.__controlFlowMap.add_arc(sem_in)
        self.__controlFlowMap.add_arc(sem_out)

    def __make_start_transition(self, t: Transition) -> CPN_Transition:
        start_t_name = get_start_transition_id(t)
        x = t.x - 50
        y = t.y
        start_t = CPN_Transition(TransitionType.SILENT, start_t_name, x, y, self.cpn_id_manager, "", ocpn_transition=t)
        self.__controlFlowMap.add_transition(start_t)
        # remove in-arcs from original transition
        # make them in-arcs of new start transition
        in_arcs = self.__petriNet.get_incoming_arcs(t.get_id())
        cpn_in_arcs = [self.__controlFlowMap.cpn_arcs_by_simple_pn_arc_id[arc.get_id()] for arc in in_arcs]
        arc: CPN_Arc
        for arc in cpn_in_arcs:
            self.__controlFlowMap.remove_arc(arc)
            new_arc = CPN_Arc(self.cpn_id_manager, arc.source, start_t, arc.annotation_text, arc.ocpn_arc)
            self.__controlFlowMap.add_arc(new_arc)
        return start_t

    def __make_control_places(self, t: Transition) -> [CPN_Place, CPN_Place]:
        control_p_name_case = get_control_place_id_case(t)
        control_p_name_event = get_control_place_id_event(t)
        x = t.x + 150
        y = t.y
        leading_type = t.get_leading_type()
        control_p_case = CPN_Place(
            control_p_name_case, x, y, self.cpn_id_manager,
            self.__colsetManager.get_object_type_colset_name(leading_type)
        )
        control_p_event = CPN_Place(control_p_name_event, x, y, self.cpn_id_manager, "INT")
        self.__controlFlowMap.add_place(control_p_case)
        self.__controlFlowMap.add_place(control_p_event)
        return control_p_case, control_p_event

    def __get_node_coordinates(self, location=1):
        x = self.running_x
        y = self.running_y * location
        self.running_x = self.running_x + 150
        return x, y

    def __add_attribute_logic(self,
                              simple_labeled_t: Transition,
                              cpn_start_t: CPN_Transition,
                              cpn_labeled_t: CPN_Transition,
                              activity: CPM_Activity):
        # for each activity attribute, make a transition to valuate the attribute,
        # and feed it into the labeled transition
        # add connections w.r.t non-aggregated dependencies
        # TODO: add connections w.r.t aggregated dependencies
        attribute_ids = self.__causalModel.get_attribute_ids_by_activity_id(activity.get_id())
        transition_id = simple_labeled_t.get_id()
        leading_type = activity.get_leading_type()
        # for each preset attribute, that is, each attribute on which some event attribute at the current
        # activity depends, we check whether a last observation exists (to guard the start transition of the
        # activity), and if it does exist, we query the last observation to be used during valuation.
        self.__current_transformed_transition_dependent_attributes = set()
        for i, attribute_id in enumerate(attribute_ids):
            self.__collect_preset_attributes(attribute_id)
        self.__control_transition_for_last_observations(cpn_start_t, leading_type)
        # As we now iterate the event attributes to build control structures, we get the last observations
        # from the start transition guard.
        attribute_domain_vars = []
        attribute_list_vars = []
        for i, attribute_id in enumerate(attribute_ids):
            x = simple_labeled_t.x + 150
            y = simple_labeled_t.y + 150 * (i + 1)
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
        object_type_id_var = self.__colsetManager.get_one_var(
            self.__colsetManager.get_object_type_ID_colset_name(leading_type))
        object_type_var = self.__colsetManager.get_one_var(
            self.__colsetManager.get_object_type_colset_name(leading_type))
        self.__eaval_parameter_tuples[activity.get_name()] = [object_type_id_var] + attribute_domain_vars
        act_guard = "{0}=((#1 {1}),{2})".format(
            eaval_var,
            object_type_var,
            ",".join(attribute_domain_vars)
        )
        cpn_labeled_t.add_guard_conjunct(act_guard)
        # distribute new last observations to global monitoring places
        for i, attribute_id in enumerate(attribute_ids):
            global_lobs_place_name = get_attribute_global_last_observation_place_name(attribute_id)
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
            preset_list_colset_name = self.__colsetManager.get_attribute_list_colset_name(in_attr_id)
            lobs_place = CPN_Place(in_attr_place_name, x + 150, y - 150 * i, self.cpn_id_manager,
                                   in_attr_colset_name)
            self.__controlFlowMap.add_place(lobs_place)
            preset_list_variable = self.__colsetManager.get_one_var(preset_list_colset_name)
            # the expression to get the last observation: the head (hd) of the second element
            # the last_observation colset is a product colset and the second element is a list
            # carrying either the last observation or nothing
            lobs_expression = "hd({0})".format(preset_list_variable)
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

    def __control_transition_for_last_observations(self, start_transition: CPN_Transition, leading_type: ObjectType):
        all_preset_attr_ids = list(self.__current_transformed_transition_dependent_attributes)
        all_preset_colset_names = [
            self.__colsetManager.get_attribute_list_colset_name(preset_attr_id)
            for preset_attr_id in all_preset_attr_ids]
        all_preset_list_variables = [
            self.__colsetManager.get_one_var(preset_colset_name)
            for preset_colset_name in all_preset_colset_names
        ]
        # for each preset attribute of some event attribute, ...
        leading_type_variable = self.__colsetManager.get_one_var(
            self.__colsetManager.get_object_type_colset_name(leading_type)
        )
        leading_type_id_variable = self.__colsetManager.get_one_var(
            self.__colsetManager.get_object_type_ID_colset_name(leading_type)
        )
        for i in range(len(all_preset_attr_ids)):
            preset_attr_id = all_preset_attr_ids[i]
            preset_list_variable = all_preset_list_variables[i]
            # ...make back and forth arcs of the last observation place with the start transition
            global_lobs_place_name = get_attribute_global_last_observation_place_name(preset_attr_id)
            global_lobs_place = self.__controlFlowMap.cpn_places_by_name[global_lobs_place_name]
            lobs_arc_inscription = "({0}, {1})".format(leading_type_id_variable, preset_list_variable)
            p_to_t = CPN_Arc(self.cpn_id_manager, global_lobs_place, start_transition, lobs_arc_inscription)
            t_to_p = CPN_Arc(self.cpn_id_manager, start_transition, global_lobs_place, lobs_arc_inscription)
            self.__controlFlowMap.add_arc(p_to_t)
            self.__controlFlowMap.add_arc(t_to_p)
            # ... make sure the activity can only be executed if there is a well-defined last observation
            # of the preset attribute.
            start_transition.add_guard_conjunct("length({0})>0".format(preset_list_variable))
        # TODO: is this still required?
        # start_transition.add_guard_conjunct("{0}=((#1) {1})".format(leading_type_id_variable, leading_type_variable))

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
            t: Transition
            for t in act_transitions:
                # Example code:
                '''
                input(v_int,v_register_patient_eaval);
                output();
                action(write_event_register_patient(v_int, reg_patient_delay(), v_register_patient_eaval));
                '''
                cpn_t = self.__controlFlowMap.cpn_transitions_by_simple_pn_transition_id[t.get_id()]
                delay_term = self.__simulationParameters.get_activity_delay_call(act_name)
                int_colset_name = "INT"
                real_colset_name = "real"
                eaval_colset_name = self.__colsetManager.get_activity_eaval_colset_name(act.get_id())
                int_var = self.__colsetManager.get_one_var(int_colset_name)
                eaval_var = self.__colsetManager.get_one_var(eaval_colset_name)
                input_variables = [int_var, eaval_var]
                input_parameters = [int_var, delay_term, eaval_var]
                input_parameters_colset_names = [int_colset_name, real_colset_name, eaval_colset_name]
                action_output = self.__colsetManager.get_one_var("TIME")
                action = get_activity_event_writer_name(act_id)
                cpn_t.add_code(action, input_variables, input_parameters, input_parameters_colset_names, action_output)

    def add_table_initializing(self):
        """
        Make sure for each activity there is an event table file (.csv) created when starting the simulation.

        """
        kickstart_transition = CPN_Transition(
            transition_type=TransitionType.SILENT,
            name=get_kickstart_transition_name(),
            x=-150,
            y=0,
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
            name=get_kickstart_place_name(),
            x=-200,
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

    def add_timing(self):
        """
        For each activity, add the execution delays etc. as operations on the token timestamps.

        """
        for act_name in self.__petriNet.get_activities():
            act_transitions = self.__petriNet.get_transitions_with_label(act_name)
            t: Transition
            for t in act_transitions:
                leading_type = t.get_leading_type()
                cpn_t = self.__controlFlowMap.cpn_transitions_by_simple_pn_transition_id[t.get_id()]
                arc: CPN_Arc
                leading_type_colset_name = self.__colsetManager.get_object_type_colset_name(leading_type)
                control_postset = [
                    arc for arc in self.__controlFlowMap.cpn_arcs
                    if arc.source == cpn_t and arc.target.colset_name == leading_type_colset_name
                ]
                for arc in control_postset:
                    annotation_text = arc.annotation_text + "@++" + self.__colsetManager.get_one_var("TIME")
                    arc.set_annotation(annotation_text)

    def make_case_generator(self):
        initial_places = self.__petriNet.get_initial_places()
        lobs_places = self.__controlFlowMap.cpn_lobs_places
        some_initial_place = initial_places[0]
        x = some_initial_place.x
        y = some_initial_place.y
        timed_int_colset_name = self.__colsetManager.get_timed_int_colset().colset_name
        # case_id_colset_name =   self.__colsetManager.get_case_id_colset().colset_name
        timedint_v = self.__colsetManager.get_one_var(timed_int_colset_name)
        # caseid_v = self.__colsetManager.get_one_var(case_id_colset_name)
        object_id_term = '"CASE" ^ Int.toString({0})'.format(timedint_v)
        object_term = '("CASE" ^ Int.toString({0}), {0})'.format(timedint_v)
        number_of_cases = self.__simulationParameters.number_of_cases
        case_generator_guard = "{0} <= {1}".format(timedint_v, str(number_of_cases))
        # case_id_declaration  = '{0} = "CASE" ^ Int.toString({1})'.format(caseid_v, timedint_v)
        initial_transition = CPN_Transition(TransitionType.SILENT, "init_t_case_generator", x, y + 200.0,
                                            self.cpn_id_manager, case_generator_guard)
        # initial_transition.add_conjunct(case_id_declaration)
        initial_transition.add_guard_conjunct(case_generator_guard)
        case_count_place = CPN_Place("init_p_case_count", x, y + 300.0, self.cpn_id_manager,
                                     colset_name=timed_int_colset_name, initmark="1")
        self.__controlFlowMap.add_transition(initial_transition)
        self.__controlFlowMap.add_place(case_count_place)
        delay_term = "ModelTime.fromInt(round(\n{0}\n(({1}))))".format(
            get_normalized_delay_from_now_function_name(ProcessTimeCategory.ARRIVAL),
            self.__simulationParameters.get_case_arrival_delay_call()
        )
        cc_to_it = CPN_Arc(self.cpn_id_manager, case_count_place, initial_transition, timedint_v)
        it_to_cc = CPN_Arc(self.cpn_id_manager, initial_transition, case_count_place,
                           timedint_v + " + 1 @++\n" + delay_term)
        self.__controlFlowMap.add_arc(cc_to_it)
        self.__controlFlowMap.add_arc(it_to_cc)
        init_p: Place
        for init_p in initial_places:
            cpn_ip = self.__controlFlowMap.cpn_places_by_simple_pn_place_id[init_p.get_id()]
            it_to_ip = CPN_Arc(self.cpn_id_manager, initial_transition, cpn_ip, object_term)
            self.__controlFlowMap.add_arc(it_to_ip)
        lobs_p: CPN_Place
        # it_to_lobs_annotation = '({0},[])'.format(caseid_v)
        it_to_lobs_annotation = '({0},[])'.format(object_id_term)
        for lobs_p in lobs_places:
            it_to_lobs = CPN_Arc(self.cpn_id_manager, initial_transition, lobs_p, it_to_lobs_annotation)
            self.__controlFlowMap.add_arc(it_to_lobs)

    def make_case_terminator(self):
        sinks = []
        for place in self.__controlFlowMap.cpn_places:
            if place.ocpn_place is not None:
                if place.ocpn_place.is_final:
                    sinks.append(place)
        lobs_places = self.__controlFlowMap.cpn_lobs_places
        for ot in self.__objectCentricityManager.get_object_types():
            ot_sinks = list(filter(lambda s: s.ocpn_place.get_object_type() == ot, sinks))
            ot_lobs_places = list(filter(lambda s: s.object_type == ot, lobs_places))
            object_type_var = self.__colsetManager.get_one_var(
                self.__colsetManager.get_object_type_colset_name(ot))
            x = sum(map(lambda s: float(s.x), ot_sinks)) / len(ot_sinks) + 100.0
            y = sum(map(lambda s: float(s.y), ot_sinks)) / len(ot_sinks)
            case_terminator = CPN_Transition(TransitionType.SILENT, "terminate_" + ot.get_id(), x, y,
                                             self.cpn_id_manager)

            for sink in ot_sinks:
                arc = CPN_Arc(self.cpn_id_manager, sink, case_terminator, object_type_var)
                self.__controlFlowMap.add_arc(arc)
            for lobs_place in ot_lobs_places:
                lobs_colset_name = lobs_place.colset_name
                lobs_var = self.__colsetManager.get_one_var(lobs_colset_name)
                case_terminator.add_guard_conjunct("(#1 {0})=(#1 {1})".format(object_type_var, lobs_var))
                arc = CPN_Arc(self.cpn_id_manager, lobs_place, case_terminator, lobs_var)
                self.__controlFlowMap.add_arc(arc)
            self.__controlFlowMap.add_transition(case_terminator)

    def make_object_type_synchronization(self):
        self.__synchronized_transitions = {
            t: {} for t in self.__controlFlowMap.get_multi_object_type_transitions()
        }
        self.__synchronize_variable_arcs_place_to_transition()
        self.__synchronize_variable_arcs_transition_to_place()
        self.__add_objectlist_propagation_for_split_transitions()

    def __synchronize_variable_arcs_place_to_transition(self):
        """
        Make sure that in front of transitions that consume multiple objects of a specific type ot,
        the tokens are selected based on object relationships to the leading object.
        This implies that the preset place of that type ot is list-structured.
        """
        place_to_transition_variable_arcs = self.__controlFlowMap.get_place_to_transition_variable_arcs()
        ca: CPN_Arc
        cp: CPN_Place
        ct: CPN_Transition
        handled_source_places = set()
        for ca in place_to_transition_variable_arcs:
            cp = ca.source
            ct = ca.target
            ot = cp.ocpn_place.get_object_type()
            if self.__controlFlowMap.is_split_in_transition(ct):
                split_out = self.__controlFlowMap.get_split_out_for_split_in(ct)
                self.__controlFlowMap.add_split_transition_pair_variable_type(ct, split_out, ot)
            if cp in handled_source_places:
                continue
            self.__convert_variable_arc_source_place_preset(ca)
            # accommodate the postset of the place to the list structure
            self.__convert_place_to_transition_variable_arc(ca)
            handled_source_places.add(cp)

    def __convert_variable_arc_source_place_preset(self, variable_arc: CPN_Arc):
        """
        The place is the source of a variable arc, so it will have a list colset.
        Make sure all incoming arcs are adapted to feed into the list.
        """
        cp: CPN_Place = variable_arc.source
        ot = cp.ocpn_place.get_object_type()
        # make the place hold a list structure
        ot_list_colset_name = self.__colsetManager.get_object_type_list_colset_name(ot)
        list_initmark = "[]"
        cp.set_colset_name(ot_list_colset_name)
        cp.set_initmark_text(list_initmark)
        # accommodate the preset of the place to the list structure
        all_arcs = self.__controlFlowMap.cpn_arcs
        cp_preset = list(filter(lambda ca: ca.target == cp, all_arcs))
        ca: CPN_Arc
        for ca in cp_preset:
            self.__controlFlowMap.remove_arc(ca)
            ct: CPN_Transition = ca.source
            ct_in = list(filter(lambda a: a.target == ct, self.__controlFlowMap.cpn_arcs))
            object_type_var = self.__colsetManager.get_one_var(
                self.__colsetManager.get_object_type_colset_name(ot))
            object_type_list_var = self.__colsetManager.get_one_var(
                self.__colsetManager.get_object_type_list_colset_name(ot))
            # Heuristic: Usually, object_type_var is bound w.r.t the incoming arcs.
            if not any(a.annotation_text == object_type_var for a in ct_in):
                # If not, just add another "buffer" place in between to assure well-defined variable bindings.
                # TODO: this needs to be tested first!!!
                # ct = self.__make_transition_to_place_buffer(ct, ca, cp, ot)
                raise NotImplementedError()
            # The place passes a list to the transition
            p_to_t_expr = object_type_list_var
            # The transition passes pack a list with a new element
            t_to_p_expr = "{0}({1},{2})".format(
                get_sorted_object_insert_function_name(ot),
                object_type_var,
                object_type_list_var)
            cp_ct = CPN_Arc(self.cpn_id_manager, cp, ct, p_to_t_expr)
            ct_cp = CPN_Arc(self.cpn_id_manager, ct, cp, t_to_p_expr)
            self.__controlFlowMap.add_arc(cp_ct)
            self.__controlFlowMap.add_arc(ct_cp)
            self.__controlFlowMap.remove_arc(ca)

    def __make_transition_to_place_buffer(self, ct: CPN_Transition, ca: CPN_Arc, cp: CPN_Place,
                                          ot: ObjectType) -> CPN_Transition:
        """
        :param ct: a transition that is incoming to the place, with unknown variables
        :param ca: the arc from the transition to the place
        :param cp: the place
        :param ot: the object type of the place
        :return: a new transition that is assured to bind the object type variable we want to use
        """
        p_buffer_name = "p_" + ct.get_id() + "_" + cp.get_id() + "_buff"
        t_buffer_name = "t_" + ct.get_id() + "_" + cp.get_id() + "_buff"
        old_annot = ca.annotation_text
        otype_colset_name = self.__colsetManager.get_object_type_colset_name(ot)
        object_type_var = self.__colsetManager.get_one_var(
            self.__colsetManager.get_object_type_colset_name(ot))
        p_buffer = CPN_Place(p_buffer_name, ct.x, str(float(ct.y) - 50.0), self.cpn_id_manager,
                             otype_colset_name, object_type=ot)
        t_buffer = CPN_Transition(TransitionType.SILENT, t_buffer_name, cp.x, str(float(cp.y) - 50.0),
                                  self.cpn_id_manager)
        ct_p_buffer = CPN_Arc(self.cpn_id_manager, ct, p_buffer, old_annot)
        p_buffer_ct = CPN_Arc(self.cpn_id_manager, p_buffer, ct, object_type_var)
        self.__controlFlowMap.remove_arc(ca)
        self.__controlFlowMap.add_place(p_buffer)
        self.__controlFlowMap.add_transition(t_buffer)
        self.__controlFlowMap.add_arc(ct_p_buffer)
        self.__controlFlowMap.add_arc(p_buffer_ct)
        return t_buffer

    def __convert_place_to_transition_variable_arc(self, variable_arc: CPN_Arc):
        """
        Accommodate the variable arc to the list structure and add guard to transition as
        synchronization mechanism w.r.t object relations around the leading type object.

        :param ot: The object type of the place (NOT the leading type)
        :param cp: The place
        """
        cp: CPN_Place = variable_arc.source
        ct: CPN_Transition = variable_arc.target
        lt = ct.ocpn_transition.get_leading_type()
        lt_colset_name = self.__colsetManager.get_object_type_colset_name(lt)
        lt_var = self.__colsetManager.get_one_var(lt_colset_name)
        ot = cp.ocpn_place.get_object_type()
        ot_list_colset_name = self.__colsetManager.get_object_type_list_colset_name(ot)
        ot_list_id_colset_name = self.__colsetManager.get_object_type_ID_list_colset_name(ot)
        ot_list_var_in, out_list_var_out = self.__colsetManager.get_some_vars(ot_list_colset_name, 2)
        conjunct = "{0}({1},{2})".format(
            get_completeness_by_relations_function_name(lt, ot),
            lt_var,
            ot_list_var_in
        )
        ct.add_guard_conjunct(conjunct)
        list_diff_term = "{0}({1},{2})".format(get_list_diff_function_name(), ot_list_var_in, out_list_var_out)
        variable_arc_in = CPN_Arc(self.cpn_id_manager, cp, ct, ot_list_var_in)
        variable_arc_out = CPN_Arc(self.cpn_id_manager, ct, cp, list_diff_term)
        self.__controlFlowMap.add_arc(variable_arc_in)
        self.__controlFlowMap.add_arc(variable_arc_out)
        self.__controlFlowMap.remove_arc(variable_arc)
        ot_at_lt_index = self.__colsetManager.get_subcol_index_by_names(lt_colset_name, ot_list_id_colset_name)
        lt_var_ot_list_access = "(#{0} {1})".format(str(ot_at_lt_index + 1), lt_var)
        action_name = get_extract_object_type_by_ids_function_name(ot)
        input_variables = [ot_list_var_in, lt_var]
        input_parameters = [ot_list_var_in, lt_var_ot_list_access]
        input_colset_names = [ot_list_colset_name, ot_list_id_colset_name]
        output = out_list_var_out
        ct.add_code(action_name, input_variables, input_parameters, input_colset_names, output)

    def __synchronize_variable_arcs_transition_to_place(self):
        """
        Make sure that the in postset of transitions that consume multiple objects of a specific type ot,
        places of the corresponding colset for ot receive a list.
        """
        transition_to_place_variable_arcs = self.__controlFlowMap.get_transition_to_place_variable_arcs()
        ca: CPN_Arc
        cp: CPN_Place
        ct: CPN_Transition
        for ca in transition_to_place_variable_arcs:
            # we will now declare that the arc propagates a corresponding list.
            ct = ca.source
            cp = ca.target
            ot = cp.ocpn_place.get_object_type()
            if self.__controlFlowMap.is_split_out_transition(ct):
                # if this transition was split (into a subpage segment with attribute logic etc.)
                # then the preset place of the transition of the object type ot contains exactly one list
                # (since the segment is a protected critical region that handles exactly one case at a time).
                # in consequence, we can just bind that one list to some variable
                # and do not need any additional guards etc.
                ot_list_colset_name = self.__colsetManager.get_object_type_list_colset_name(ot)
                ot_list_colset_var = self.__colsetManager.get_one_var(ot_list_colset_name)
                ca.set_annotation(ot_list_colset_var)
            else:
                # otherwise, the objects bound at the OCPN transition
                # are stored in a list that have been bound to a variable with a different name
                # (see the code segment at __convert_place_to_transition_variable_arc).
                ot_list_colset_name = self.__colsetManager.get_object_type_list_colset_name(ot)
                _, ot_list_colset_var2 = self.__colsetManager.get_some_vars(ot_list_colset_name, 2)
                ca.set_annotation(ot_list_colset_var2)

    def __add_objectlist_propagation_for_split_transitions(self):
        """
        We have the lists of objects readily bound to variables at the in-part and the out-part of the split transitions
        (See __synchronize_variable_arcs_place_to_transition and __synchronize_variable_arcs_transition_to_place).
        Now we just add a place in between split-in and split-out for propagation.
        All attribute computations etc. do not depend on the variable objects,
        but are controlled via the leading type object.
        """
        split_transition_pairs = self.__controlFlowMap.get_split_transition_pairs_variable_types()
        ca: CPN_Arc
        cp: CPN_Place
        split_in: CPN_Transition
        split_out: CPN_Transition
        for (split_in, split_out), var_types in split_transition_pairs.items():
            for ot in var_types:
                propagation_place_name = split_in.get_id() + "_propagate_" + ot.get_id()
                # add a bit of random coordinate variation so that in case multiple nodes are stacked
                # on top of each other can be identified visually
                rx = random.randint(-15, 15)
                ry = random.randint(-15, 15)
                px = str(round((float(split_in.x)+float(split_out.x))/2 + rx))
                py = str(round((float(split_in.y)+float(split_out.y))/2 + ry))
                ot_colset_list_name = self.__colsetManager.get_object_type_list_colset_name(ot)
                propagation_place = CPN_Place(propagation_place_name, px, py, self.cpn_id_manager, ot_colset_list_name, object_type=ot)
                self.__controlFlowMap.add_place(propagation_place)
                _, in_var = self.__colsetManager.get_some_vars(ot_colset_list_name, 2)
                out_var = self.__colsetManager.get_one_var(ot_colset_list_name)
                split_in_to_pp = CPN_Arc(self.cpn_id_manager, split_in, propagation_place, in_var)
                pp_to_split_in = CPN_Arc(self.cpn_id_manager, propagation_place, split_out, out_var)
                self.__controlFlowMap.add_arc(split_in_to_pp)
                self.__controlFlowMap.add_arc(pp_to_split_in)



















