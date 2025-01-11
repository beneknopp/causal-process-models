from object_centric.object_centric_petri_net import ObjectCentricPetriNet
from object_centric.object_centric_petri_net import ObjectCentricPetriNet as OCPN, ObjectCentricPetriNetArc as Arc, \
    ObjectCentricPetriNetPlace as Place, ObjectCentricPetriNetTransition as Transition
from process_model.petri_net import ArcDirection
from simulation_model.colset import ColsetManager, get_object_type_colset_name
from simulation_model.control_flow.map import ControlFlowMap
from simulation_model.cpn_utils.cpn_arc import CPN_Arc
from simulation_model.cpn_utils.cpn_place import CPN_Place
from simulation_model.cpn_utils.cpn_transition import TransitionType, CPN_Transition
from simulation_model.cpn_utils.xml_utils.cpn_id_managment import CPN_ID_Manager


class PetriNetCaster():

    def __init__(self,
                 petriNet: ObjectCentricPetriNet,
                 cpn_id_manager: CPN_ID_Manager,
                 colsetManager: ColsetManager,
                 controlFlowMap: ControlFlowMap
                 ):
        self.__controlFlowMap = controlFlowMap
        self.__colsetManager = colsetManager
        self.cpn_id_manager = cpn_id_manager
        self.__petriNet = petriNet

    def cast(self):
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
                get_object_type_colset_name(place_type)
            )
            cpn_place = self.__convert_simple_pn_place(place)
            cpn_transition = self.__convert_ocpn_transition(transition)
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
        colset_name = get_object_type_colset_name(place_type)
        initmark = None
        ################# TODO Testcode Testcode Testcode ########################
        if colset_name == "C_orders" and simple_pn_place.is_initial:
            initmark = '[("o1", 3, ["i1", "i2", "i3"]) @ 1, ("o2", 3, ["i4", "i5"]) @ 10]'
        if colset_name == "C_items" and simple_pn_place.is_initial:
            initmark = '[("i1", 3, "o1")@1,("i2", 3, "o1")@1, ("i3", 2, "o1")@20, ("i4", 2, "o2")@10, ("i5", 2, "o2")@15]'
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

    def __convert_ocpn_transition(self, ocpn_transition: Transition):
        simple_pn_transition_id = ocpn_transition.get_id()
        if simple_pn_transition_id in self.__controlFlowMap.cpn_transitions_by_simple_pn_transition_id:
            return self.__controlFlowMap.cpn_transitions_by_simple_pn_transition_id[simple_pn_transition_id]
        labeling_function = self.__petriNet.get_labels()
        labeled_transition_ids = labeling_function.get_keys()
        is_labeled = simple_pn_transition_id in labeled_transition_ids
        transition_type = TransitionType.ACTIVITY if is_labeled else TransitionType.SILENT
        label = simple_pn_transition_id if not is_labeled else labeling_function.get_label(simple_pn_transition_id)
        cpn_transition = CPN_Transition(transition_type, label,
                                        ocpn_transition.x + 300, ocpn_transition.y,
                                        self.cpn_id_manager, ocpn_transition=ocpn_transition)

        if is_labeled:
            # this then is the transition we use as a transaction transition later.
            self.__controlFlowMap.add_transaction_transition_for_ocpn_transition(ocpn_transition, cpn_transition)
        else:
            self.__controlFlowMap.add_transition(cpn_transition, simple_pn_transition_id)
        return cpn_transition
