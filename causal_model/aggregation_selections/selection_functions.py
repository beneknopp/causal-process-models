from abc import ABC

from causal_model.aggregation_selections.aggregation_selections import AggregationSelection, AuxiliaryFunction
from causal_model.causal_process_structure import AttributeRelation
from object_centric.object_centric_functions import get_project_object_to_many_relations_name
from simulation_model.colset import get_object_type_ID_list_colset_name, \
    get_attribute_system_aggregation_colset_name_list, get_object_type_ID_colset_name, \
    get_attribute_all_observations_colset_name


class SelectionBy_toManyRelationsLastObservation(AggregationSelection, ABC):

    def __init__(self, name, r: AttributeRelation):
        super().__init__(name, r)

    def __get_g_function_name(self):
        return "g_" + self.get_function_name()

    def __get_h_function_name(self):
        return "h_" + self.get_function_name()

    def get_g_auxiliary(self):
        in_object_type_id_list_colset_name = \
            get_object_type_ID_list_colset_name(self.object_type_in)
        allobs_colset_name = \
            get_attribute_all_observations_colset_name(self.attribute_in.get_id())
        g_function_name = self.__get_g_function_name()
        g_function_sml  = "fun \n" \
                          "{0}(_, []) = [] |\n" \
                          "{0}([], _) = [] | \n" \
                          "{0}(yid::yids: {1}, ys: {2}) = \n" \
                          "{3}(yid, ys)^^{0}(yids,ys)".format(
            g_function_name,
            in_object_type_id_list_colset_name,
            allobs_colset_name,
            self.__get_h_function_name()
        )
        return AuxiliaryFunction(
            function_name=g_function_name,
            sml_code=g_function_sml
        )

    def get_h_auxiliary(self):
        in_object_type_id_colset_name = \
            get_object_type_ID_colset_name(self.object_type_in)
        allobs_colset_name = \
            get_attribute_all_observations_colset_name(self.attribute_in.get_id())
        h_function_name = self.__get_h_function_name()
        h_function_sml  = "fun \n{0}(_, []) = [] | {0}(yid: {1}, y::ys: {2}) = \nif (yid = (#1 (#1 y))) then [#3 y] \nelse {0}(yid, ys)".format(
            h_function_name,
            in_object_type_id_colset_name,
            allobs_colset_name
        )
        return AuxiliaryFunction(
            function_name=h_function_name,
            sml_code=h_function_sml
        )

    def make_auxiliary_functions(self):
        auxiliary_functions: list[AuxiliaryFunction] = [
            self.get_h_auxiliary(),
            self.get_g_auxiliary(),
        ]
        return auxiliary_functions

    def to_SML(self):
        '''
        Example: (where #2 projects x to object relations to type Y
        f(x, _, ys) = g(#2 x, ys)

        g(_, []) = []
        | g(yid::yids, ys) = h(yid, ys)::g(yids, ys)

        h(_, []) = [] | h(yid, y::ys) = (if (yid = (#1 (#1 y)))) then [#3 y] else h(yid, ys)

        Here, assume that domain value observation is at position 3 of y

        '''
        return "fun {0}({1}) =\n {2}({3}(x), ys)".format(
            self.get_function_name(),
            self.get_parameter_string(),
            self.__get_g_function_name(),
            get_project_object_to_many_relations_name(
                self.object_type_out,
                self.object_type_in
            )
        )