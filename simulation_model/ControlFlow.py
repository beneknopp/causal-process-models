from causal_model.CausalProcessModel import CausalProcessModel
from causal_model.CausalProcessStructure import CPM_Attribute, CPM_Activity
from process_model.PetriNet import PetriNet, SimplePetriNetPlace, SimplePetriNetTransition, SimplePetriNetArc
from simulation_model.Colset import ColsetManager
from simulation_model.cpn_utils.CPN_Arc import CPN_Arc
from simulation_model.cpn_utils.CPN_Place import CPN_Place
from simulation_model.cpn_utils.CPN_Transition import CPN_Transition, TransitionType
from simulation_model.cpn_utils.xml_utils.CPN_ID_Manager import CPN_ID_Manager


class ControlFlowMap:
    cpn_places: list[CPN_Place] = list()
    cpn_transitions: list[CPN_Transition] = list()
    cpn_nodes_by_id: dict = dict()
    cpn_places_by_id: dict = dict()
    cpn_places_by_simple_pn_place_id: dict = dict()
    cpn_transitions_by_simple_pn_transition_id: dict = dict()
    cpn_transitions_by_id: dict = dict()
    cpn_arcs: list[CPN_Arc] = list()
    cpn_arcs_by_id: dict = dict()
    cpn_arcs_by_simple_pn_arc_id: dict = dict()

    def __init__(self):
        pass

    def add_place(self, place: CPN_Place, simple_place_id: str = None):
        place_id = place.get_id()
        if place_id in self.cpn_places_by_id:
            raise ValueError("Place already added")
        self.cpn_places_by_id[place_id] = place
        self.cpn_nodes_by_id[place_id] = place
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
        self.cpn_arcs = list(filter(lambda a: not(a.get_id() == arc_id), self.cpn_arcs))
        self.cpn_arcs_by_id = {key: value for key, value in self.cpn_arcs_by_id.items() if key != arc_id}
        self.cpn_arcs_by_simple_pn_arc_id = {
            key: value for key, value in self.cpn_arcs_by_simple_pn_arc_id.items() if value.get_id() != arc_id}

def get_attribute_place_name(attribute_id, suffix):
    return "p_" + "_".join(attribute_id.split(" ")) + "_" + suffix


def get_start_transition_id(t: SimplePetriNetTransition):
    return "t_start_" + t.get_id()

def get_attr_valuation_transition_name(attr_id: str):
    return "t_V_" + attr_id


def get_control_place_id(t: SimplePetriNetTransition):
    return "p_control_" + t.get_id()


class ControlFlowManager:
    # some coordinates to put nodes somewhere
    # TODO: use some graph layouting algorithm
    running_x = 0
    running_y = -100

    def __init__(self,
                 cpn_id_manager: CPN_ID_Manager,
                 petriNet: PetriNet,
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
        # TODO: make generic this is just for testing timed behaviours
        initial_marking_case_ids_with_time = ['"{0}@{1}"'.format(cid, i * 1000) for i, cid in
                                              enumerate(self.initial_marking_case_ids)]
        initmark = "[" + ",".join(initial_marking_case_ids_with_time) + "]"
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
        cpn_transition = CPN_Transition(transition_type, label, simple_pn_transition.x, simple_pn_transition.y,
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
        x, y = self.__get_node_coordinates()
        semaphore_place = CPN_Place(
            "global_sem", x, y, self.cpn_id_manager,
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
        lobs_place_name = get_attribute_place_name(attribute.get_id(), "LAST")
        lobs_colset_name = self.__colsetManager.get_attribute_last_observation_colset_name(
            attribute.get_id()
        )
        x, y = self.__get_node_coordinates()
        initmark = "[" + ",".join(['("{0}",[])'.format(cid) for cid in self.initial_marking_case_ids]) + "]"
        lobs_place = CPN_Place(lobs_place_name, x, y, self.cpn_id_manager, lobs_colset_name, False, initmark)
        self.__controlFlowMap.add_place(lobs_place)

    def __convert_transition(self, t: SimplePetriNetTransition, activity: CPM_Activity):
        start_t = self.__make_start_transition(t)
        control_p = self.__make_control_place(t)
        cpn_t = self.__controlFlowMap.cpn_transitions_by_simple_pn_transition_id[t.get_id()]
        caseid_var = self.__colsetManager.get_one_var(self.__colsetManager.get_case_id_colset().colset_name)
        control_a1 = CPN_Arc(self.cpn_id_manager, start_t, control_p, caseid_var)
        control_a2 = CPN_Arc(self.cpn_id_manager, control_p, cpn_t, caseid_var)
        self.__controlFlowMap.add_arc(control_a1)
        self.__controlFlowMap.add_arc(control_a2)
        self.__add_attribute_logic(t, start_t, cpn_t, activity)

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

    def __make_control_place(self, t: SimplePetriNetTransition) -> CPN_Place:
        control_p_name = get_control_place_id(t)
        x = t.x + 50
        y = t.y
        control_p = CPN_Place(control_p_name, x, y, self.cpn_id_manager,
                              self.__colsetManager.get_case_id_colset().colset_name)
        self.__controlFlowMap.add_place(control_p)
        return control_p

    def __get_node_coordinates(self):
        x = self.running_x
        y = self.running_y
        self.running_x = self.running_x + 50
        return x, y

    def __add_attribute_logic(self, simple_labeled_t: SimplePetriNetTransition, cpn_start_t: CPN_Transition,
                              cpn_labeled_t: CPN_Transition, activity: CPM_Activity):
        # for each activity attribute, make a transition to valuate the attribute,
        # and feed it into the labeled transition
        # add connections w.r.t non-aggregated dependencies
        # TODO: add connections w.r.t aggregated dependencies
        attribute_ids = self.__causalModel.get_attribute_ids_by_activity_id(activity.get_id())
        for i, attribute_id in enumerate(attribute_ids):
            x = simple_labeled_t.x + 50
            y = simple_labeled_t.y + 50*(i+1)
            self.__make_attribute_transition(attribute_id, x, y)

    def __make_attribute_transition(self, attribute_id: str, x, y):
        attr_t_name = get_attr_valuation_transition_name(attribute_id)
        attr_t = CPN_Transition(TransitionType.SILENT, attr_t_name, x, y, self.cpn_id_manager,
                                self.__causalModel.get_attribute_valuation())
