from pandas import DataFrame

from object_centric.object_centric_petri_net import ObjectCentricPetriNet
from object_centric.object_centric_petri_net import ObjectCentricPetriNet as OCPN, ObjectCentricPetriNetArc as Arc, \
    ObjectCentricPetriNetPlace as Place, ObjectCentricPetriNetTransition as Transition
from object_centric.object_centricity_management import ObjectCentricityManager
from object_centric.object_type_structure import ObjectType
from process_model.petri_net import ArcDirection
from simulation_model.colset import ColsetManager, get_object_type_colset_name, get_object_type_ID_colset_name, \
    get_object_type_ID_list_colset_name
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
                 controlFlowMap: ControlFlowMap,
                 objectCentricityManager: ObjectCentricityManager,
                 initialMarking: dict[ObjectType, DataFrame]
                 ):
        self.__controlFlowMap = controlFlowMap
        self.__colsetManager = colsetManager
        self.cpn_id_manager = cpn_id_manager
        self.__petriNet = petriNet
        self.__objectCentricityManager = objectCentricityManager
        self.__initialMarking = initialMarking

    def cast(self):
        """
        Wrap the Petri net into a CPN.
        """
        places = self.__petriNet.get_places()
        transitions = self.__petriNet.get_transitions()
        self.__add_variable_arc_buffers()
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
            source = cpn_place      if arc_direction is ArcDirection.P2T else cpn_transition
            target = cpn_transition if arc_direction is ArcDirection.P2T else cpn_place
            cpn_arc = CPN_Arc(self.cpn_id_manager, source, target, v_object_type, is_variable_arc=arc.is_variable())
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
        object_type = simple_pn_place.get_object_type()
        initmark = "initmark_" + object_type.get_id()
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

    def __add_variable_arc_buffers(self):
        '''
        For outgoing variable arcs, add a buffer structure.
        This avoids difficulties with handling list structures.
        '''
        arcs = self.__petriNet.arcs
        for arc in arcs:
            arc_direction = arc.get_direction()
            if arc.is_variable() and arc_direction is ArcDirection.T2P:
                original_place: Place = arc.get_place()
                original_transition = arc.get_transition()
                x_p = float(original_place.x)
                y_p = float(original_place.y)
                x_t = float(original_transition.x)
                y_t = float(original_transition.y)
                p_BUFF_x = (x_t + 0.4 * (x_t - x_p))
                p_BUFF_y = (y_t + 0.4 * (y_t - y_p))
                t_BUFF_x = (x_t + 0.6 * (x_t - x_p))
                t_BUFF_y = (y_t + 0.6 * (y_t - y_p))
                p_BUFFER = Place(node_id="p_" + arc.get_id() + "_buff", x = p_BUFF_x, y = p_BUFF_y,
                                 object_type=original_place.get_object_type(), is_initial=False, is_final=False)
                t_BUFFER = Transition(node_id="p_" + arc.get_id() + "_buff", x = t_BUFF_x, y = t_BUFF_y,
                                      leading_type=original_place.get_object_type())
                original_t2p_buff = Arc(original_transition, p_BUFFER, is_variable=True)
                p_buff2t_buff = Arc(p_BUFFER, t_BUFFER)
                t_buff2original_p = Arc(t_BUFFER, original_place)
                self.__petriNet.add_place(p_BUFFER)
                self.__petriNet.add_transition(t_BUFFER)
                self.__petriNet.add_arcs([original_t2p_buff, p_buff2t_buff, t_buff2original_p])
                self.__petriNet.remove_arc(arc)

