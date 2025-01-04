from itertools import product

from causal_model.causal_process_structure import CPM_Attribute, CPM_Attribute_Domain, CPM_Categorical_Attribute
from utils.math import cumulative_distribution
from utils.validators import validate_condition


class ValuationParameter:

    def __init__(self, attribute: CPM_Attribute):
        self.__attribute = attribute

    def get_attribute(self):
        return self.__attribute

    def get_attribute_domain(self):
        return self.__attribute.get_domain()


class ValuationParameters:

    def __validate(self):
        validate_condition(all(
            isinstance(p, ValuationParameter) for p in self.__valuation_parameters_list))
        validate_condition(all(
            isinstance(a, CPM_Attribute) for a in [p.get_attribute() for p in self.__valuation_parameters_list]
        ))

    def __init__(self, valuation_parameters_list: list[ValuationParameter]):
        self.__valuation_parameters_list = valuation_parameters_list
        self.__validate()

    def get_valuation_parameters_list(self):
        return self.__valuation_parameters_list


class AttributeValuation:

    def __init__(self,
                 valuation_parameters: ValuationParameters,
                 outcome_attribute: CPM_Attribute):
        self.valuation_parameters = valuation_parameters
        self.outcome_attribute = outcome_attribute

    def parse(self):
        raise NotImplementedError()

    def get_function_name(self):
        return "valuate_" + "_".join(self.outcome_attribute.get_id().split(" "))

    def to_SML(self):
        raise NotImplementedError()

    def get_call(self):
        raise NotImplementedError()


def define_uniform_probability_mapping(valuation_parameters: ValuationParameters,
                                       outcome: CPM_Categorical_Attribute) \
        -> dict[tuple, dict[str, float]]:
    outcome_labels = outcome.get_labels()
    udist = {
        l: 1 / len(outcome_labels) for l in outcome_labels
    }
    vp: ValuationParameter
    vp_list = valuation_parameters.get_valuation_parameters_list()
    label_lists = [vp.get_attribute().get_labels() for vp in vp_list]
    cartesian_product = list(product(*label_lists))
    umap = {
        c: udist
        for c in cartesian_product
    }
    return umap


class BayesianValuation(AttributeValuation):
    outcome_attribute: CPM_Categorical_Attribute

    def __validate_valuation_parameters(
            self, valuation_parameters: ValuationParameters):
        """
        1. Assert that all parameters are categorical (Colset type "WITH").
        # TODO
        2. Assert that all input tuples correspond to the correct domains.
        3. Assert that outcome is well-defined for any input tuple (if has_complete_mappings).
        4. Assert that probabilities for all input tuples sum to 1.

        :raises ValueError if otherwise
        """
        # 1
        x: ValuationParameter
        validate_condition(all(
            x.get_attribute_domain() == CPM_Attribute_Domain.CATEGORICAL
            for x in valuation_parameters.get_valuation_parameters_list()
        ))

    def __init__(self, valuation_parameters: ValuationParameters,
                 outcome_attribute: CPM_Categorical_Attribute,
                 probability_mappings=None,
                 has_complete_mappings: bool = True):
        """
        Initialize the probabilistic Bayesian mapper with predefined mappings.

        :param valuation_parameters: The ValuationParameters
        :param outcome_attribute: The codomain of the valuation function
        :param probability_mappings: The probabilities for all possible input tuples, that is,
            a dictionary where keys are tuples representing parameter states, and values are
            dictionaries mapping outcomes to their probabilities. Tuples are ordered w.r.t.
            the parameter ordering of valuation_parameters. Example:
            {
             ("Sunny", "Heavy"): {"HighRisk": 0.7, "MediumRisk": 0.3},
             ("Rainy", "Light"): {"LowRisk": 1.0}
             ... }
             If this is None, a uniform distribution will be auto-defined for all input configurations.
        :param has_complete_mappings: Whether probability_mappings should define valuations for
        all (exponentially many) input configurations. If this is False, the simulation may not be
        deadlock-free.
        """
        self.__validate_valuation_parameters(valuation_parameters)
        super().__init__(valuation_parameters, outcome_attribute)
        if probability_mappings is None:
            probability_mappings = define_uniform_probability_mapping(
                valuation_parameters, outcome_attribute)
        self.__probability_mappings = probability_mappings
        self.__has_complete_mappings = has_complete_mappings
        self.__validate_valuation_function()

    def __validate_valuation_function(self):
        """
        Make sure that the valuation function makes sense.

        """
        parameter_list = self.valuation_parameters.get_valuation_parameters_list()
        outcome_attribute = self.outcome_attribute
        admissible_outcomes = outcome_attribute.get_labels()
        for key, probs in self.__probability_mappings.items():
            uncovered_labels = [label for label in admissible_outcomes if label not in probs.keys()]
            validate_condition(not len(uncovered_labels),
                               ('Key {0} does not specify probabilities for label(s) {1}.'
                                + 'Please make all probabilities explicit, even if they are 0.').format(
                                   key, uncovered_labels))
            for i in range(len(key)):
                label = key[i]
                admissible_labels = parameter_list[i].get_attribute().get_labels()
                validate_condition(label in admissible_labels,
                                   'Key {0} has invalid label "{1}"'.format(key, label))
                validate_condition(abs(1 - sum(probs.values())) < 0.0001,
                                   "Probabilities at key {0} do not sum to 1".format(key))

    def __get_function_name(self):
        return super(BayesianValuation, self).get_function_name()

    def to_SML(self):
        function_name = self.__get_function_name()
        parameter_string = self.__get_parameter_string()
        function_body = self.__get_function_body()
        return "fun {0}({1}) = {2}".format(function_name, parameter_string, function_body)

    def get_call(self):
        function_name = self.__get_function_name()
        return lambda parameters: "{0}({1})".format(
            function_name,
            ",".join(parameters)
        )

    def __get_parameter_string(self):
        return ",".join(["x{0}".format(str(i)) for i in range(len(
            self.valuation_parameters.get_valuation_parameters_list()))])

    def __get_function_body(self):
        '''
        Example:
        if  x1=A andalso x2=B then (let val x=uniform(0.0,1.0) in (
            if x < 0.3 then A else if x < 0.9 then B else C) end;
        )
        else if x1=A andalso x2=C then (let val x=uniform(0.0,1.0) in (
            if x < 0.3 then A else B) end;
        )
        else B;
        '''
        case_sub_bodies = []
        for key, dist in self.__probability_mappings.items():
            case_sub_body = self.__get_case_sub_body(key, dist)
            case_sub_bodies.append(case_sub_body)
        function_body = "else ".join(case_sub_bodies)
        # unreachable code, just for valid syntax
        function_body += 'else ' + self.outcome_attribute.get_labels()[0]
        return function_body

    def __get_case_sub_body(self, key_tuple: tuple, dist: dict) -> str:
        """
        Example:
        if  x1=A andalso x2=B then  (let val x=uniform(0.0,1.0) in
        ( if x < P0 then V0 else if x < P0+P1 then V1 else V2) end;)
        """
        if not len(key_tuple):
            key_body = "true"
        else:
            key_body = " andalso ".join(['x{0}={1}'.format(
                str(i),
                k
            ) for i, k in enumerate(list(key_tuple))])
        if len(dist) == 1:
            dist_body = list(dist.values())[0]
        else:
            cum_dist = cumulative_distribution(dist)
            # if x < P0 then V0 else if x < P0+P1 then V1 else V2 ...
            cum_dist_body = ""
            cum_dist_items = list(cum_dist.items())
            for v, p in cum_dist_items[:-1]:
                cum_dist_body += 'if p < {0} then {1} else '.format(
                    str(p), v
                )
            lastv, _ = cum_dist_items[-1]
            cum_dist_body += lastv
            dist_body = "(let val p=uniform(0.0,1.0) in ({0}) end)".format(
                cum_dist_body
            )
        return "if {0} then {1} ".format(key_body, dist_body)
