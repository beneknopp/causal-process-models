import random

from pandas import DataFrame

from causal_model.causal_process_model import CausalProcessModel
from causal_model.causal_process_structure import CPM_Attribute, CPM_Activity, CPM_Domain_Type
from object_centric.object_centric_functions import get_sorted_object_insert_function_name, \
    get_completeness_by_relations_function_name, get_extract_object_type_by_ids_function_name, \
    get_match_one_relation_function_name
from object_centric.object_centric_petri_net import ObjectCentricPetriNet as OCPN, ObjectCentricPetriNetPlace as Place, ObjectCentricPetriNetTransition as Transition
from object_centric.object_centricity_management import ObjectCentricityManager
from object_centric.object_type_structure import ObjectType
from process_model.petri_net import ArcDirection
from simulation_model.colset import ColsetManager, get_object_type_colset_name, get_object_type_ID_colset_name, \
    get_object_type_list_colset_name, get_object_type_ID_list_colset_name
from simulation_model.control_flow.control_flow_sub_manager.causal_model_merger import CausalModelMerger
from simulation_model.control_flow.map import ControlFlowMap, get_ocpn_transition_control_transition_name, \
    get_control_place_id_case, get_control_place_id_event, get_attribute_global_last_observation_place_name, \
    get_attribute_global_all_observations_place_name, get_kickstart_transition_name, get_kickstart_place_name, \
    get_ot_initial_transition_name, get_ot_initial_place_name
from simulation_model.control_flow.control_flow_sub_manager.petri_net_caster import PetriNetCaster
from simulation_model.cpn_utils.cpn_arc import CPN_Arc
from simulation_model.cpn_utils.cpn_place import CPN_Place
from simulation_model.cpn_utils.cpn_transition import CPN_Transition, TransitionType
from simulation_model.cpn_utils.xml_utils.cpn_id_managment import CPN_ID_Manager
from simulation_model.functions import get_activity_event_writer_name, get_activity_event_table_initializer_name, \
    get_normalized_delay_from_now_function_name, get_list_diff_function_name
from simulation_model.simulation_parameters import SimulationParameters
from simulation_model.timing import ProcessTimeCategory


class ControlFlowManager:


    def __init__(self,
                 cpn_id_manager: CPN_ID_Manager,
                 petriNet: OCPN,
                 causalModel: CausalProcessModel,
                 simulationParameters: SimulationParameters,
                 objectCentricityManager: ObjectCentricityManager,
                 colsetManager: ColsetManager,
                 initialMarking: dict[ObjectType, DataFrame]
                 ):
        self.cpn_id_manager = cpn_id_manager
        self.__petriNet = petriNet
        self.__causalModel = causalModel
        self.__simulationParameters = simulationParameters
        self.__objectCentricityManager = objectCentricityManager
        self.__colsetManager = colsetManager
        self.__controlFlowMap = ControlFlowMap()
        self.__initialMarking = initialMarking

    def merge_models(self):
        self.cast_petri_net()
        self.__make_case_initializer()
        self.__split_activity_transitions()
        self.merge_causal_model()

    def cast_petri_net(self):
        """
        Wrap the Petri net into a CPN.
        """
        petri_net_caster = PetriNetCaster(
            self.__petriNet,
            self.cpn_id_manager,
            self.__colsetManager,
            self.__controlFlowMap,
            self.__objectCentricityManager,
            self.__initialMarking
        )
        petri_net_caster.cast()

    def merge_causal_model(self):
        causal_model_merger = CausalModelMerger(
            cpn_id_manager=self.cpn_id_manager,
            controlFlowMap=self.__controlFlowMap,
            petriNet=self.__petriNet,
            causalModel=self.__causalModel,
            colsetManager=self.__colsetManager
        )
        causal_model_merger.merge_in_causal_model()

    def __split_activity_transitions(self):
        cm_activities = self.__causalModel.get_activities()
        for act in cm_activities:
            act_name = act.get_name()
            act_transitions = self.__petriNet.get_transitions_with_label(act_name)
            t: Transition
            for t in act_transitions:
                self.__split_activity_transition(t, act)

    def __split_activity_transition(self, ocpn_transition: Transition, act: CPM_Activity):
        t_CONTROL = self.__make_control_transition(ocpn_transition)
        t_TRANSACT = self.__controlFlowMap.get_transaction_transition_for_ocpn_transition(ocpn_transition)
        t_TRANSACT.set_activity(act)
        self.__controlFlowMap.add_split_transition_pair(t_CONTROL, t_TRANSACT)

    def __make_control_transition(self, ocpn_transition: Transition) -> CPN_Transition:
        """
        This creates the start transition for an activity transition.
        This transition controls the execution of the activity, i.e., checks the bindings and
        checks for required attribute values being present.

        :param t: the labeled OCPN_Transition
        :return: the resulting start transition (CPN_Transition)
        """
        x = ocpn_transition.x - 50
        y = ocpn_transition.y
        control_transition_name = get_ocpn_transition_control_transition_name(ocpn_transition)
        t_CONTROL = CPN_Transition(TransitionType.SILENT,
                                 control_transition_name,
                                 x, y,
                                 self.cpn_id_manager,
                                 ocpn_transition=ocpn_transition)
        self.__controlFlowMap.add_control_transition_for_ocpn_transition(ocpn_transition, t_CONTROL)
        # remove in-arcs from original transition
        # make them in-arcs of new start transition
        in_arcs = self.__petriNet.get_incoming_arcs(ocpn_transition.get_id())
        cpn_in_arcs = [self.__controlFlowMap.cpn_arcs_by_simple_pn_arc_id[arc.get_id()] for arc in in_arcs]
        arc: CPN_Arc
        for arc in cpn_in_arcs:
            self.__controlFlowMap.remove_arc(arc)
            new_arc = CPN_Arc(self.cpn_id_manager, arc.source, t_CONTROL, arc.expression, arc.delay, arc.is_variable_arc)
            self.__controlFlowMap.add_arc(new_arc)
        return t_CONTROL


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
            transaction_transitions = self.__controlFlowMap.get_transaction_transitions()
            for ocpn_transition in act_transitions:
                # Example code:
                '''
                input(v_int,v_register_patient_eaval);
                output();
                action(write_event_register_patient(v_int, reg_patient_delay(), v_register_patient_eaval));
                '''
                t_TRANSACT = self.__controlFlowMap.get_transaction_transition_for_ocpn_transition(ocpn_transition)
                leading_type = act.get_leading_type()
                delay_term = self.__simulationParameters.get_activity_delay_call(act_name)
                int_colset_name = "INT"
                real_colset_name = "real"
                case_colset_name    = get_object_type_colset_name(leading_type)
                case_id_colset_name = get_object_type_ID_colset_name(leading_type)
                act_attrs = self.__causalModel.get_local_attributes_for_activity_id(act_id)
                eaval_vars          = self.__colsetManager.get_all_attribute_domain_colset_vars(act_attrs)
                eaval_colsetnames   = self.__colsetManager.get_all_attribute_domain_colset_names(act_attrs)
                int_var = self.__colsetManager.get_one_var(int_colset_name)
                case_var = self.__colsetManager.get_one_var(case_colset_name)
                case_id_term = "#1 {0}".format(case_var)
                input_variables = [int_var, case_var] + eaval_vars
                input_parameters                = [int_var, case_id_term, delay_term] + eaval_vars
                input_parameters_colset_names   = [int_colset_name, case_id_colset_name, real_colset_name] + eaval_colsetnames
                action_output = self.__colsetManager.get_one_var("TIME")
                action = get_activity_event_writer_name(act_id)
                t_TRANSACT.add_code(action, input_variables, input_parameters, input_parameters_colset_names, action_output,
                               self.__objectCentricityManager.get_object_types(), is_event_writing = True)

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
        For each transition, check whether we added timing logic to it, and distribute the delay terms
        across the postset with respect to the object types.

        """
        for ca in self.__controlFlowMap.cpn_arcs:
            if ca.orientation is ArcDirection.P2T:
                continue
            ct = ca.transend
            ot = ca.get_object_type()
            ot_at_ct_delay = ct.get_object_type_delay_variable(ot)
            if ot_at_ct_delay is not None:
                ca.set_delay(ot_at_ct_delay)

    def make_case_terminator(self):
        sinks = []
        for place in self.__controlFlowMap.cpn_places:
            ocpn_place = place.ocpn_place
            if ocpn_place is not None:
                if ocpn_place.is_final:
                    sinks.append(place)
        lobs_places = self.__controlFlowMap.cpn_lobs_places.values()
        ots = self.__objectCentricityManager.get_object_types()
        for ot in ots:
            ot_sinks = list(filter(lambda s: s.ocpn_place.get_object_type() == ot, sinks))
            ot_lobs_places = list(filter(lambda s: s.object_type == ot, lobs_places))
            object_type_var = self.__colsetManager.get_one_var(
                get_object_type_colset_name(ot))
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
        self.__synchronize_variable_arcs_place_to_transition()
        self.__synchronize_variable_arcs_transition_to_place()
        self.__add_object_list_propagation_for_split_transitions()
        self.__synchronize_multiplicity_one_arcs_place_to_transition()
        self.__synchronize_multiplicity_one_arcs_transition_to_place()
        self.__add_object_single_propagation_for_split_transitions()

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
            ot = ca.get_object_type()
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
        ot = variable_arc.get_object_type()
        # make the place hold a list structure
        ot_list_colset_name = get_object_type_list_colset_name(ot)
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
                get_object_type_colset_name(ot))
            object_type_list_var = self.__colsetManager.get_one_var(
                get_object_type_list_colset_name(ot))
            #ct = self.__make_transition_to_place_buffer(ct, ca, cp, ot)
            # The place passes a list to the transition
            p_to_t_expr = object_type_list_var
            # The transition passes pack a list with a new element
            t_to_p_expr = "{0}({1},{2})".format(
                get_sorted_object_insert_function_name(ot),
                object_type_var,
                object_type_list_var)
            cp_ct = CPN_Arc(self.cpn_id_manager, cp, ct, p_to_t_expr)
            ct_cp = CPN_Arc(self.cpn_id_manager, ct, cp, t_to_p_expr, ca.delay)
            self.__controlFlowMap.add_arc(cp_ct)
            self.__controlFlowMap.add_arc(ct_cp)
            self.__controlFlowMap.remove_arc(ca)

    def __convert_place_to_transition_variable_arc(self, variable_arc: CPN_Arc):
        """
        Accommodate the variable arc to the list structure and add guard to transition as
        synchronization mechanism w.r.t object relations around the leading type object.

        :param ot: The object type of the place (NOT the leading type)
        :param cp: The place
        """
        cp: CPN_Place = variable_arc.source
        t_CONTROL: CPN_Transition = variable_arc.target
        lt = t_CONTROL.ocpn_transition.get_leading_type()
        lt_colset_name = get_object_type_colset_name(lt)
        lt_var = self.__colsetManager.get_one_var(lt_colset_name)
        ot = variable_arc.get_object_type()
        ot_list_colset_name     = get_object_type_list_colset_name(ot)
        ot_list_id_colset_name  = get_object_type_ID_list_colset_name(ot)
        ot_list_var_in, out_list_var_out = self.__colsetManager.get_some_vars(ot_list_colset_name, 2)
        conjunct = "{0}({1},{2})".format(
            get_completeness_by_relations_function_name(lt, ot),
            lt_var,
            ot_list_var_in
        )
        t_CONTROL.add_guard_conjunct(conjunct)
        list_diff_term = "{0}({1},{2})".format(get_list_diff_function_name(), ot_list_var_in, out_list_var_out)
        variable_arc_in = CPN_Arc(self.cpn_id_manager, cp, t_CONTROL, ot_list_var_in)
        variable_arc_out = CPN_Arc(self.cpn_id_manager, t_CONTROL, cp, list_diff_term)
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
        t_CONTROL.add_code(action_name, input_variables, input_parameters, input_colset_names, output)

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
            ot = cp.get_object_type()
            if self.__controlFlowMap.is_split_out_transition(ct):
                # if this transition was split (into a subpage segment with attribute logic etc.)
                # then the preset place of the transition of the object type ot contains exactly one list
                # (since the segment is a protected critical region that handles exactly one case at a time).
                # in consequence, we can just bind that one list to some variable
                # and do not need any additional guards etc.
                ot_list_colset_name = get_object_type_list_colset_name(ot)
                ot_list_colset_var = self.__colsetManager.get_one_var(ot_list_colset_name)
            else:
                # otherwise, the objects bound at the OCPN transition
                # are stored in a list that have been bound to a variable with a different name
                # (see the code segment at __convert_place_to_transition_variable_arc).
                ot_list_colset_name = get_object_type_list_colset_name(ot)
                _, ot_list_colset_var = self.__colsetManager.get_some_vars(ot_list_colset_name, 2)
            ca.set_expression(ot_list_colset_var)

    def __add_object_list_propagation_for_split_transitions(self):
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
                px, py = self.__get_in_between_node_coordinates(split_in, split_out)
                ot_colset_list_name = get_object_type_list_colset_name(ot)
                propagation_place = CPN_Place(propagation_place_name, px, py, self.cpn_id_manager, ot_colset_list_name,
                                              object_type=ot)
                self.__controlFlowMap.add_place(propagation_place)
                _, in_var = self.__colsetManager.get_some_vars(ot_colset_list_name, 2)
                out_var = self.__colsetManager.get_one_var(ot_colset_list_name)
                split_in_to_pp = CPN_Arc(self.cpn_id_manager, split_in, propagation_place, in_var)
                pp_to_split_in = CPN_Arc(self.cpn_id_manager, propagation_place, split_out, out_var)
                self.__controlFlowMap.add_arc(split_in_to_pp)
                self.__controlFlowMap.add_arc(pp_to_split_in)

    def __synchronize_multiplicity_one_arcs_place_to_transition(self):
        non_leading_type_place_to_transition_simple_arcs = self.__controlFlowMap.get_non_leading_type_place_to_transition_simple_arcs(
            self.__objectCentricityManager.get_object_type_structure())
        for arc in non_leading_type_place_to_transition_simple_arcs:
            leading_type = arc.get_transition_object_type()
            non_leading_type = arc.get_place_object_type()
            transition = arc.get_transition()
            function_name = get_match_one_relation_function_name(leading_type, non_leading_type)
            leading_type_var = self.__colsetManager.get_one_var(
                get_object_type_colset_name(leading_type))
            non_leading_type_var = self.__colsetManager.get_one_var(
                get_object_type_colset_name(non_leading_type))
            conjunct = "{0}({1},{2})".format(function_name, leading_type_var, non_leading_type_var)
            transition.add_guard_conjunct(conjunct)

    def __synchronize_multiplicity_one_arcs_transition_to_place(self):
        non_leading_type_transition_to_place_simple_arcs = self.__controlFlowMap.get_non_leading_type_transition_to_place_simple_arcs(
            self.__objectCentricityManager.get_object_type_structure())
        for arc in non_leading_type_transition_to_place_simple_arcs:
            ct = arc.transend
            non_leading_type = arc.get_place_object_type()
            delay_var = ct.get_object_type_delay_variable(non_leading_type)
            if delay_var is not None:
                arc.update_delay(delay_var)

    def __add_object_single_propagation_for_split_transitions(self):
        split_transition_pairs = self.__controlFlowMap.get_split_transition_pairs()
        for split_pair in split_transition_pairs:
            non_leading_types = self.__controlFlowMap.get_non_leading_types_for_split_pair(
                split_pair, self.__objectCentricityManager.get_object_type_structure())
            split_in, split_out = split_pair
            for non_leading_type in non_leading_types:
                propagation_place_name = split_in.get_id() + "_propagate_" + non_leading_type.get_id()
                ot_colset_list_name = get_object_type_colset_name(non_leading_type)
                px, py = self.__get_in_between_node_coordinates(split_in, split_out)
                propagation_place = CPN_Place(propagation_place_name, px, py, self.cpn_id_manager, ot_colset_list_name,
                                              object_type=non_leading_type)
                self.__controlFlowMap.add_place(propagation_place)
                var = self.__colsetManager.get_one_var(ot_colset_list_name)
                split_in_to_pp = CPN_Arc(self.cpn_id_manager, split_in, propagation_place, var)
                pp_to_split_in = CPN_Arc(self.cpn_id_manager, propagation_place, split_out, var)
                self.__controlFlowMap.add_arc(split_in_to_pp)
                self.__controlFlowMap.add_arc(pp_to_split_in)

    @staticmethod
    def __get_in_between_node_coordinates(n1, n2):
        # add a bit of random coordinate variation so that in case multiple nodes are stacked
        # on top of each other can be identified visually
        rx = random.randint(-15, 15)
        ry = random.randint(-15, 15)
        px = str(round((float(n1.x) + float(n2.x)) / 2 + rx))
        py = str(round((float(n1.y) + float(n2.y)) / 2 + ry))
        return px, py

    def get_cpn_places(self):
        return self.__controlFlowMap.cpn_places

    def get_cpn_transitions(self):
        return self.__controlFlowMap.cpn_transitions

    def get_cpn_arcs(self):
        return self.__controlFlowMap.cpn_arcs

    def __make_case_initializer(self):
        initial_places = self.__petriNet.get_initial_places()
        for p_init in initial_places:
            p_INIT_OLD: CPN_Place
            p_INIT_OLD = self.__controlFlowMap.cpn_places_by_simple_pn_place_id[p_init.get_id()]
            # Assume we have one initial place per object type.
            ot = p_INIT_OLD.get_ocpn_place().get_object_type()
            x1 = str(float(p_INIT_OLD.x) - 50)
            x2 = str(float(p_INIT_OLD.x) - 100)
            y = p_INIT_OLD.y
            ot_colset_name = get_object_type_colset_name(ot)
            ot_colset_var = self.__colsetManager.get_one_var(ot_colset_name)
            t_INIT = CPN_Transition(
                TransitionType.SILENT, get_ot_initial_transition_name(ot),
                x1, y,
                self.cpn_id_manager)
            p_INIT_NEW = CPN_Place(
                get_ot_initial_place_name(ot),
                x2, y,
                self.cpn_id_manager, ot_colset_name,
                initmark=p_INIT_OLD.initmark, object_type=ot
            )
            p_INIT_OLD.set_initmark_text("")
            p_INIT_OLD.is_initial = False
            p_INIT_NEW.is_initial = True
            a_INIT   = CPN_Arc(self.cpn_id_manager, p_INIT_NEW, t_INIT, ot_colset_var)
            a_SECOND = CPN_Arc(self.cpn_id_manager, t_INIT, p_INIT_OLD, ot_colset_var)
            # Assume we have one initial place per object type (so this here happens only once).
            self.__controlFlowMap.add_case_initialization_transition(t_INIT, ot)
            self.__controlFlowMap.add_place(p_INIT_NEW)
            self.__controlFlowMap.add_arc(a_INIT)
            self.__controlFlowMap.add_arc(a_SECOND)
