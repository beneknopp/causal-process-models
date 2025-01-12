from object_centric.object_centric_functions import get_project_object_type_to_ids_function_sml, \
    get_project_object_type_to_ids_function_name, get_extract_object_type_by_ids_function_name, \
    get_extract_object_type_by_ids_function_sml, get_sorted_object_insert_function_sml, \
    get_sorted_object_insert_function_name, get_completeness_by_relations_function_sml, \
    get_completeness_by_relations_function_name, get_match_one_relation_function_sml, \
    get_match_one_relation_function_name, get_project_object_to_many_relations_name, \
    get_project_object_to_many_relations_sml
from object_centric.object_type_structure import ObjectTypeStructure, Multiplicity
from object_centric.object_centric_petri_net import ObjectCentricPetriNet as OCPN, \
    ObjectCentricPetriNetPlace as Place, ObjectCentricPetriNetArc as Arc
from process_model.petri_net import ArcDirection
from simulation_model.colset import ColsetManager
from simulation_model.cpn_utils.xml_utils.cpn_id_managment import CPN_ID_Manager


class ObjectCentricityManager:

    # TODO:
    # Consistency between Petri net and OT-Structure
    def __validate(self):
        pass

    def __init__(self,
                 cpn_id_manager: CPN_ID_Manager,
                 petriNet: OCPN,
                 objectTypeStructure: ObjectTypeStructure,
                 colsetManager: ColsetManager
                 ):
        self.cpn_id_manager = cpn_id_manager
        self.__petriNet = petriNet
        self.__objectTypeStructure = objectTypeStructure
        self.__colsetManager = colsetManager
        self.__validate()

    def get_object_type_sml_functions(self):
        object_type_sml_functions = []
        for ot in self.__objectTypeStructure.get_object_types():
            object_type_sml_functions.append((get_project_object_type_to_ids_function_name(ot),
                                              get_project_object_type_to_ids_function_sml(ot)))
            object_type_sml_functions.append((get_extract_object_type_by_ids_function_name(ot),
                                              get_extract_object_type_by_ids_function_sml(ot)))
            object_type_sml_functions.append((get_sorted_object_insert_function_name(ot),
                                              get_sorted_object_insert_function_sml(ot)))
        for r in self.__objectTypeStructure.get_object_type_relations():
            ot1 = r.get_ot1()
            m1 = r.get_m1()
            m2 = r.get_m2()
            ot2 = r.get_ot2()
            if m2 is Multiplicity.MANY:
                object_type_sml_functions.append((get_completeness_by_relations_function_name(ot1, ot2),
                                                  get_completeness_by_relations_function_sml(ot1, ot2, self.__colsetManager)))
                object_type_sml_functions.append((get_project_object_to_many_relations_name(ot1, ot2),
                                                  get_project_object_to_many_relations_sml(ot1, ot2, self.__colsetManager)))
            if m1 is Multiplicity.MANY:
                object_type_sml_functions.append((get_completeness_by_relations_function_name(ot2, ot1),
                                                  get_completeness_by_relations_function_sml(ot2, ot1, self.__colsetManager)))
                object_type_sml_functions.append((get_project_object_to_many_relations_name(ot2, ot1),
                                                  get_project_object_to_many_relations_sml(ot2, ot1, self.__colsetManager)))
            if m1 is Multiplicity.ONE:
                object_type_sml_functions.append((get_match_one_relation_function_name(ot2, ot1),
                                                  get_match_one_relation_function_sml(ot2, ot1, self.__colsetManager)))
            if m2 is Multiplicity.ONE:
                object_type_sml_functions.append((get_match_one_relation_function_name(ot1, ot2),
                                                  get_match_one_relation_function_sml(ot1, ot2, self.__colsetManager)))
        return object_type_sml_functions


    def get_object_types(self):
        return self.__objectTypeStructure.get_object_types()

    def get_object_type_structure(self):
        return self.__objectTypeStructure

    def get_to_1_relations_for_object_type(self, object_type):
        return self.__objectTypeStructure.get_to_1_relations_for_object_type(object_type)

    def get_to_N_relations_for_object_type(self, object_type):
        return self.__objectTypeStructure.get_to_N_relations_for_object_type(object_type)

