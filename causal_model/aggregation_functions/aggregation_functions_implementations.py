from abc import ABC

from causal_model.aggregation_functions.aggregation_functions import AggregationFunction
from causal_model.causal_process_structure import REAL_DOMAIN, CPM_Domain_Type, AttributeRelation
from utils.sml_coding import AuxiliaryFunction
from utils.validators import validate_condition


class MaxMinDiff(AggregationFunction, ABC):

    def __validate(self):
        validate_condition(self.input_domain.domain_type is CPM_Domain_Type.REAL)

    def __init__(self, name, r: AttributeRelation):
        super().__init__(name, r, REAL_DOMAIN)

    def __get_max_auxiliary_name(self):
        return "max_for_" + self.get_function_name()

    def __get_min_auxiliary_name(self):
        return "min_for_" + self.get_function_name()

    def __get_max_auxiliary_function(self):
        '''
        fun max([]) = 0 | max(x::nil) = x | max(x::(y::ys): C_DOM_list) = if x > y then max(x::ys) else max(y::ys)
        '''
        max_auxiliary_name = self.__get_max_auxiliary_name()
        max_auxiliary_sml  = "fun \n" \
                             "{0}([]) = 0.0 | \n" \
                             "{0}(x::nil) = x | \n" \
                             "{0}(x::(y::ys): {1} list) = \n" \
                             "if x > y \n" \
                             "then {0}(x::ys) \n" \
                             "else {0}(y::ys)".format(
            max_auxiliary_name,
            self.input_domain_colset_name,
        )
        return AuxiliaryFunction(
            function_name=max_auxiliary_name,
            sml_code=max_auxiliary_sml
        )

    def __get_min_auxiliary_function(self):
        '''
        fun min([]) = 0 | min(x::nil) = x | min(x::(y::ys): C_DOM list) = if x < y then min(x::ys) else min(y::ys)
        '''
        min_auxiliary_name = self.__get_min_auxiliary_name()
        min_auxiliary_sml  = "fun \n" \
                             "{0}([]) = 0.0 | \n" \
                             "{0}(x::nil) = x | \n" \
                             "{0}(x::(y::ys): {1} list) = \n" \
                             "if x < y \n" \
                             "then {0}(x::ys) \n" \
                             "else {0}(y::ys)".format(
            min_auxiliary_name,
            self.input_domain_colset_name,
        )
        return AuxiliaryFunction(
            function_name=min_auxiliary_name,
            sml_code=min_auxiliary_sml
        )

    def make_auxiliary_functions(self):
        return [
            self.__get_max_auxiliary_function(),
            self.__get_min_auxiliary_function()
        ]

    def to_SML(self):
        return "fun {0}({1}) = \n" \
               "let \nval vmax = {2}(xs) \nval vmin = {3}(xs) \nin \n vmax - vmin \nend".format(
            self.get_function_name(),
            self.get_parameter_string(),
            self.__get_max_auxiliary_name(),
            self.__get_min_auxiliary_name()
        )
