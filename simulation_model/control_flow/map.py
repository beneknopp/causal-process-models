from causal_model.causal_process_structure import CPM_Attribute
from object_centric.object_centric_petri_net import ObjectCentricPetriNetTransition as Transition
from object_centric.object_type_structure import ObjectTypeStructure, Multiplicity, ObjectType
from process_model.petri_net import ArcDirection
from simulation_model.cpn_utils.cpn_arc import CPN_Arc
from simulation_model.cpn_utils.cpn_place import CPN_Place
from simulation_model.cpn_utils.cpn_transition import CPN_Transition


def get_attribute_place_name(attribute_id: str, suffix):
    return "p_" + "_".join(attribute_id.split(" ")) + "_" + suffix


def get_transition_attribute_place_name(transition_id: str, attribute_id: str, suffix):
    return "p_" + "_".join(transition_id.split(" ")) + "_" + "_".join(attribute_id.split(" ")) + "_" + suffix


def get_ocpn_transition_control_transition_name(ocpn_transition: Transition):
    return "t_CONTROL_" + ocpn_transition.get_id()


def get_ocpn_transition_transaction_transition_name(ocpn_transition: Transition):
    return "t_TRANSACT_" + ocpn_transition.get_id()


def get_ot_initial_transition_name(ot: ObjectType):
    return "t_INIT_" + ot.get_id()


def get_ot_initial_place_name(ot: ObjectType):
    return "p_INIT_" + ot.get_id()


def get_attribute_global_last_observation_place_name(attribute_id):
    """
    Canonical name of the unique place in the net where the last observation of some event
    attribute is being monitored.

    :param attribute_id: the attribute being monitored
    :return: the canonical name
    """
    return get_attribute_place_name(attribute_id, "LAST")


def get_attribute_global_all_observations_place_name(attribute_id):
    """
    Canonical name of the unique place in the net where all observations of some event
    attributes are being collected for the purpose of aggregation.

    :param attribute_id: the attribute being collected
    :return: the canonical name
    """
    return get_attribute_place_name(attribute_id, "ALL")


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


def get_control_selection_place_name(attr_VALUATED: CPM_Attribute, attr_AGGREGATED: CPM_Attribute):
    return "p_CONTROL_SELECTION_" + attr_AGGREGATED.get_id() + "_FOR_" + attr_VALUATED.get_id()


def get_aggregation_selection_transition_name(attr_VALUATED: CPM_Attribute, attr_AGGREGATED: CPM_Attribute):
    return "t_SELECT_" + attr_AGGREGATED.get_id() + "_FOR_" + attr_VALUATED.get_id()


def get_selected_values_place_name(attr_VALUATED: CPM_Attribute, attr_AGGREGATED: CPM_Attribute):
    return "p_SELECTION_" + attr_AGGREGATED.get_id() + "_FOR_" + attr_VALUATED.get_id()


def get_aggregation_transition_name(attr_VALUATED: CPM_Attribute, attr_AGGREGATED: CPM_Attribute):
    return "t_AGGREGATE_" + attr_AGGREGATED.get_id() + "_FOR_" + attr_VALUATED.get_id()


def get_aggregated_values_place_name(attr_VALUATED: CPM_Attribute, attr_AGGREGATED: CPM_Attribute):
    return "p_AGGREGATED_" + attr_AGGREGATED.get_id() + "_FOR_" + attr_VALUATED.get_id()


class ControlFlowMap:
    # some coordinates to put nodes somewhere
    # TODO: use some graph layouting algorithm
    running_x = 0
    running_y = -100

    def get_node_coordinates(self, location=1):
        x = self.running_x
        y = self.running_y * location
        self.running_x = self.running_x + 150
        return x, y

    def __init__(self):
        """
        This class maintains all CPN nodes and arcs, provides getters for various filtering criteria,
        and finally is called by the XML serializer to pass over the set of nodes and arcs.
        """
        self.cpn_places: list[CPN_Place] = list()
        self.cpn_lobs_places: dict[CPM_Attribute, CPN_Place] = dict()
        self.cpn_allobs_places: dict[CPM_Attribute, CPN_Place] = dict()
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
        self.ot_initial_transitions: dict[ObjectType, CPN_Transition] = dict()
        self.ocpn_transition_to_control_transition = dict()
        self.ocpn_transition_to_transaction_transition = dict()
        self.split_transitions_in_to_out: dict[CPN_Transition, CPN_Transition] = dict()
        self.split_transitions_out_to_in: dict[CPN_Transition, CPN_Transition] = dict()
        self.split_transition_pairs_variable_types: dict[
            tuple[CPN_Transition, CPN_Transition], set[ObjectType]] = dict()
        self.aggregation_selection_transitions: dict[CPM_Attribute, dict[CPM_Attribute, CPN_Transition]] = dict()
        self.aggregation_transitions: dict[CPM_Attribute, dict[CPM_Attribute, CPN_Transition]] = dict()

    def add_place(self, place: CPN_Place, simple_place_id: str = None):
        place_id = place.get_id()
        place_name = place.get_name()
        if place_id in self.cpn_places_by_id \
                or place_name in self.cpn_places_by_name \
                or simple_place_id in self.cpn_places_by_simple_pn_place_id:
            raise ValueError("Place already added")
        self.cpn_places_by_id[place_id] = place
        self.cpn_nodes_by_id[place_id] = place
        self.cpn_places_by_name[place_name] = place
        self.cpn_places.append(place)
        if simple_place_id is not None:
            self.cpn_places_by_simple_pn_place_id[simple_place_id] = place
        return place

    def add_transition(self, transition: CPN_Transition, simple_transition_id: str = None):
        transition_id = transition.get_id()
        if transition_id in self.cpn_transitions_by_id:
            raise ValueError("Transition already added")
        self.cpn_transitions_by_id[transition_id] = transition
        self.cpn_nodes_by_id[transition_id] = transition
        self.cpn_transitions.append(transition)
        if simple_transition_id is not None:
            self.cpn_transitions_by_simple_pn_transition_id[simple_transition_id] = transition
        return transition

    def add_arc(self, arc: CPN_Arc, simple_pn_arc_id=None):
        arc_id = arc.get_id()
        if arc_id in self.cpn_arcs_by_id:
            raise ValueError("Arc already added")
        self.cpn_arcs_by_id[arc_id] = arc
        self.cpn_arcs.append(arc)
        if simple_pn_arc_id is not None:
            self.cpn_arcs_by_simple_pn_arc_id[simple_pn_arc_id] = arc
        return arc

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

    def add_lobs_place(self, p_LOBS: CPN_Place, attribute: CPM_Attribute):
        self.add_place(p_LOBS)
        self.cpn_lobs_places[attribute] = p_LOBS

    def add_allobs_place(self, p_ALLOBS: CPN_Place, attribute: CPM_Attribute):
        self.add_place(p_ALLOBS)
        self.cpn_allobs_places[attribute] = p_ALLOBS

    def get_allobs_place(self, attribute: CPM_Attribute):
        return self.cpn_allobs_places[attribute]

    def get_mapped_variable_arcs(self):
        variable_arcs = list(filter(lambda a: a.is_variable_arc, self.cpn_arcs))
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

    def get_split_transition_pairs(self):
        return list(self.split_transition_pairs_variable_types.keys())

    def add_split_transition_pair_variable_type(self, split_in: CPN_Transition, split_out: CPN_Transition,
                                                ot: ObjectType):
        self.split_transition_pairs_variable_types[(split_in, split_out)].add(ot)

    def get_place_to_transition_arcs(self):
        return list(filter(lambda a: a.orientation == ArcDirection.P2T, self.cpn_arcs))

    def get_transition_to_place_arcs(self):
        return list(filter(lambda a: a.orientation == ArcDirection.T2P, self.cpn_arcs))

    @staticmethod
    def __filter_non_leading_type_simple_arcs(arcs, ot_struct: ObjectTypeStructure):
        # 1. retain arcs that connect a typed place
        # 2. retain arcs that are non-variable and that connect to a leading type different from the place type
        arcs = list(filter(lambda a:
                           (a.get_place().ocpn_place is not None) and
                           (a.get_transition_object_type() != a.get_object_type()) and
                           (ot_struct.has_multiplicity(a.get_transition_and_place_object_types(), Multiplicity.ONE))
                           , arcs))
        return arcs

    def get_non_leading_type_place_to_transition_simple_arcs(self, ot_struct: ObjectTypeStructure) -> list[CPN_Arc]:
        arcs = self.get_place_to_transition_arcs()
        arcs = self.__filter_non_leading_type_simple_arcs(arcs, ot_struct)
        return arcs

    def get_non_leading_type_transition_to_place_simple_arcs(self, ot_struct: ObjectTypeStructure) -> list[CPN_Arc]:
        arcs = self.get_transition_to_place_arcs()
        arcs = self.__filter_non_leading_type_simple_arcs(arcs, ot_struct)
        return arcs

    def get_non_leading_types_for_split_pair(self, split_pair: tuple[CPN_Transition, CPN_Transition],
                                             ot_struct: ObjectTypeStructure):
        split_in, _ = split_pair
        arcs = self.cpn_arcs
        arcs = list(filter(lambda a: a.transend == split_in, arcs))
        arcs = self.__filter_non_leading_type_simple_arcs(arcs, ot_struct)
        non_leading_types = set(map(lambda a: a.get_place_object_type(), arcs))
        return non_leading_types

    def add_control_transition_for_ocpn_transition(self, ocpn_transition: Transition,
                                                   control_transition: CPN_Transition):
        self.add_transition(control_transition, ocpn_transition.get_id())
        self.ocpn_transition_to_control_transition[ocpn_transition] = control_transition

    def add_transaction_transition_for_ocpn_transition(self, ocpn_transition: Transition,
                                                       transaction_transition: CPN_Transition):
        self.add_transition(transaction_transition, ocpn_transition.get_id())
        self.ocpn_transition_to_transaction_transition[ocpn_transition] = transaction_transition

    def get_control_transition_for_ocpn_transition(self, ocpn_transition: Transition):
        return self.ocpn_transition_to_control_transition[ocpn_transition]

    def get_transaction_transition_for_ocpn_transition(self, ocpn_transition: Transition):
        return self.ocpn_transition_to_transaction_transition[ocpn_transition]

    def get_transaction_transitions(self):
        return list(self.ocpn_transition_to_transaction_transition.values())

    def add_case_initialization_transition(self, t_INIT: CPN_Transition, ot: ObjectType):
        self.add_transition(t_INIT)
        self.ot_initial_transitions[ot] = t_INIT

    def get_case_initialization_transition(self, ot: ObjectType):
        return self.ot_initial_transitions[ot]

    def get_initial_transition(self, ot: ObjectType):
        return self.ot_initial_transitions[ot]

    def add_aggregation_selection_transition(self, t_SELECT: CPN_Transition, attr_VALUATED: CPM_Attribute,
                                             attr_AGGREGATED: CPM_Attribute):
        t_SELECT = self.add_transition(t_SELECT)
        aggr_sel_map = self.aggregation_selection_transitions
        if attr_VALUATED not in aggr_sel_map:
            aggr_sel_map[attr_VALUATED] = dict()
        aggr_sel_map[attr_VALUATED][attr_AGGREGATED] = t_SELECT
        return t_SELECT

    def add_aggregation_transition(self, t_AGGREGATE: CPN_Transition, attr_VALUATED: CPM_Attribute,
                                   attr_AGGREGATED: CPM_Attribute):
        t_AGGREGATE = self.add_transition(t_AGGREGATE)
        aggr_map = self.aggregation_transitions
        if attr_VALUATED not in aggr_map:
            aggr_map[attr_VALUATED] = dict()
        aggr_map[attr_VALUATED][attr_AGGREGATED] = t_AGGREGATE
        return t_AGGREGATE
