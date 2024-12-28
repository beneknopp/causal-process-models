from causal_model.CausalProcessModel import CausalProcessModel
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

    def add_arc(self, arc: CPN_Arc):
        arc_id = arc.get_id()
        if arc_id in self.cpn_arcs_by_id:
            raise ValueError("Arc already added")
        self.cpn_arcs_by_id[arc_id] = arc
        self.cpn_arcs.append(arc)


class ControlFlowManager:

    def __init__(self,
                 cpn_id_manager: CPN_ID_Manager,
                 petriNet: PetriNet,
                 causalModel: CausalProcessModel,
                 colsetManager: ColsetManager
                ):
        self.cpn_id_manager = cpn_id_manager
        self.__petriNet = petriNet
        self.__causalModel = causalModel
        self.__colsetManager = colsetManager
        self.__controlFlowMap = ControlFlowMap()

    def merge_models(self):
        self.cast_petri_net()
        #self.merge_causal_model()

    def cast_petri_net(self):
        """
        Wrap the Petri net into a CPN
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
            self.__controlFlowMap.add_arc(cpn_arc)
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
        initmark = "`[1@0]" if is_initial else ""
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