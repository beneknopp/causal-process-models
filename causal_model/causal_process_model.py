from causal_model.aggregation_functions.aggregation_functions import AggregationFunction
from causal_model.aggregation_selections.aggregation_selections_implementations import AggregationSelection
from causal_model.causal_process_structure import CausalProcessStructure, AttributeRelation, CPM_Attribute, \
    CPM_Domain_Type, CPM_Activity
from causal_model.valuation import AttributeValuation
from utils.validators import validate_condition


class AggregationSelections:

    def __validate(self):
        validate_condition(
            all(isinstance(r, AttributeRelation) for r in self.__relations))
        validate_condition(
            all(isinstance(r, AggregationSelection) for r in self.__selections))

    def __init__(self, relationsToSelection: dict):
        self.__relations = list(relationsToSelection.keys())
        self.__selections = list(relationsToSelection.values())
        self.relationsToSelection = relationsToSelection

    def get_relations(self):
        return self.__relations

    def get_smls(self):
        smls = []
        for selection in self.relationsToSelection.values():
            selection: AggregationSelection
            for aux in selection.auxiliary_functions:
                smls.append((aux.get_function_name(), aux.to_SML()))
            smls.append((selection.get_function_name(), selection.to_SML()))
        return smls


class AggregationFunctions:

    def __validate(self):
        validate_condition(
            all(isinstance(r, AttributeRelation) for r in self.__relations))
        validate_condition(
            all(isinstance(r, AggregationFunction) for r in self.__aggregations))

    def __init__(self, relationsToAggregation: dict):
        self.__relations = list(relationsToAggregation.keys())
        self.__aggregations = list(relationsToAggregation.values())
        self.relationsToAggregation = relationsToAggregation

    def get_relations(self):
        return self.__relations

    def get_smls(self):
        smls = []
        for aggregation in self.relationsToAggregation.values():
            aggregation: AggregationFunction
            for aux in aggregation.auxiliary_functions:
                smls.append((aux.get_function_name(), aux.to_SML()))
            smls.append((aggregation.get_function_name(), aggregation.to_SML()))
        return smls


class AttributeValuations:

    def __validate(self):
        validate_condition(
            all(isinstance(r, str) for r in self.__attribute_ids))
        validate_condition(
            all(isinstance(v, AttributeValuation) for v in self.__attributeIdToValuation.values()))

    def __init__(self, attributeToValuation: dict[CPM_Attribute, AttributeValuation]):
        """
        This class prescribes a valuation for each attribute in a causal model.
        :param attributeIdToValuation: a map from attribute id to an AttributeValuation
        """
        self.__attributes = list(attributeToValuation.keys())
        self.__attribute_ids = list([k.get_id() for k in attributeToValuation.keys()])
        self.__valuations = list(attributeToValuation.values())
        self.__attributeToValuation = attributeToValuation
        self.__attributeIdToValuation = {k.get_id(): v for k, v in attributeToValuation.items()}
        self.__validate()

    def sort(self, sorted_attribute_ids):
        """
        Make sure the sorting of the parameters corresponds to the way attributes are sorted in the causal model.
        This function is called after initializing the ValuationParameters class within a new causal model.
        This is to facilitate manually using the API (i.e., user does not need to worry about passing attributes in the right order).

        :param sorted_attribute_ids: All attributes in the causal model, sorted
        """
        sorted_parameter_attribute_ids = list(filter(lambda a: a in self.__attribute_ids, sorted_attribute_ids))
        self.__attribute_ids = sorted_parameter_attribute_ids

    def get_attribute_ids(self):
        return self.__attribute_ids

    def get_attribute_valuation_list(self):
        return list(self.__attributeIdToValuation.values())

    def get_attribute_valuation(self, attribute_id) -> AttributeValuation:
        return self.__attributeIdToValuation.get(attribute_id)

    def get_all_valuation_parameter_domains(self):
        all_parameter_domains = set()
        for valuation in self.__valuations:
            valuation_parameters = valuation.valuation_parameters
            valuation_parameters_list = valuation_parameters.get_valuation_parameters_list()
            for valuation_parameter in valuation_parameters_list:
                all_parameter_domains.add(valuation_parameter.get_domain())
        return all_parameter_domains


class CausalProcessModel:

    def __validate(self):
        cs_attributes = self.__CS.get_attributes()
        cs_attribute_ids = self.__CS.get_attribute_ids()
        cs_aggregated_relations = self.__CS.get_aggregated_relations()
        v_attribute_ids = self.__V.get_attribute_ids()
        sagg_relations = self.__Sagg.get_relations()
        fagg_relations = self.__Fagg.get_relations()
        valuated_attributes_not_in_model = [
            attr_id for attr_id in v_attribute_ids if attr_id not in cs_attribute_ids]
        validate_condition(
            not valuated_attributes_not_in_model,
            "There are valuated attributes ({0}) not specified in the causal structure.".format(
                valuated_attributes_not_in_model))
        attributes_without_valuation = [
            attr.get_id() for attr in cs_attributes
            if attr.get_id() not in v_attribute_ids
               and attr.get_domain_type() not in CPM_Domain_Type.get_independent_domain_types()]
        validate_condition(
            not attributes_without_valuation,
            "There are attributes ({0}) without valuation.".format(
                attributes_without_valuation))
        validate_condition(
            all(r in cs_aggregated_relations for r in sagg_relations))
        validate_condition(
            all(r in cs_aggregated_relations for r in fagg_relations))
        validate_condition(
            all(r in sagg_relations for r in fagg_relations))
        validate_condition(
            all(r in fagg_relations for r in sagg_relations))
        for attribute_id in self.__V.get_attribute_ids():
            valuation = self.__V.get_attribute_valuation(attribute_id)
            valuation_params = valuation.valuation_parameters.get_valuation_parameters_list()
            continue
            #TODO: bugfixing
            params_not_in_causal_structure = [param.get_attribute().get_id() for param in valuation_params if
                                              param.get_attribute() not in self.get_attributes()]
            validate_condition(
                not len(params_not_in_causal_structure),
                'There are attributes "{0}" that are used to valuate attribute "{1}", but those were not found among '
                'the attributes listed in the causal structure.'.format(params_not_in_causal_structure, attribute_id))
            params_not_covered_in_relations = [param.get_attribute().get_id() for param in valuation_params
                                               if not self.has_relation(param.get_attribute().get_id(), attribute_id)]
            validate_condition(
                not len(params_not_covered_in_relations),
                'There are attributes "{0}" that are used to valuate attribute "{1}", but the relation between those '
                'attributes and "{1}" is not listed in the causal structure.'.format(
                    params_not_covered_in_relations, attribute_id))
        # TODO: make sure valuation parameters are consistent with relationships indicated in causal structure

    def __init__(self,
                 CS: CausalProcessStructure,
                 Sagg: AggregationSelections,
                 Fagg: AggregationFunctions,
                 V: AttributeValuations
                 ):
        """
        Define a causal model over a causal structure.

        :param CS: The CausalProcessStructure.
        :param Sagg: An AggregationSelection for each aggregated dependency in CS.
        :param Fagg: An AggregationFunction for each aggregated dependency in CS.
        :param V: An AttributeValuation for each attribute in CS.
        """
        self.__CS = CS
        self.__Sagg = Sagg
        self.__Fagg = Fagg
        self.__V = V
        self.__validate()

    def get_aggregation_selection(self):
        return self.__Sagg

    def get_aggregation_function(self):
        return self.__Fagg

    def get_attribute_valuations(self):
        return self.__V

    def get_activities(self):
        return self.__CS.get_activities()

    def get_attribute_activities(self):
        return self.__CS.get_attribute_activities()

    def get_attributes_with_non_aggregated_dependencies(self):
        return self.__CS.get_attributes_with_non_aggregated_dependencies()

    def get_attributes_with_aggregated_dependencies(self):
        return self.__CS.get_attributes_with_aggregated_dependencies()

    def get_activity_names(self):
        acts = self.__CS.get_activities()
        act_ids = [act.get_name() for act in acts]
        return act_ids

    def get_attributes(self):
        return self.__CS.get_attributes()

    def get_attribute_names(self):
        attrs = self.__CS.get_attributes()
        attr_names = [attr.get_name() for attr in attrs]
        return attr_names

    def get_relations(self):
        return self.__CS.get_relations()

    def add_activity(self, activity_name):
        return self.__CS.add_activity(activity_name)

    def to_string(self):
        s = ""
        s += self.__CS.print()
        return s

    def get_attribute_ids_by_activity_id(self, activity_id):
        return self.__CS.get_attribute_ids_by_activity_id(activity_id)

    def get_valuation_functions_sml(self):
        av: AttributeValuation
        return [(av.get_function_name(), av.to_SML()) for av in self.__V.get_attribute_valuation_list()]

    def get_preset(self, attribute: CPM_Attribute, aggregated: bool = None) -> list[AttributeRelation]:
        return self.__CS.get_preset(attribute, aggregated)

    def get_attributes_for_activity_id(self, act_id):
        return self.__CS.get_attributes_for_activity_id(act_id)

    def has_relation(self, attr_in_id: str, attr_out_id: str, is_aggregated: bool = None):
        return self.__CS.has_relation(attr_in_id, attr_out_id, is_aggregated)

    def get_activity_for_attribute_id(self, attribute_id):
        return self.__CS.get_activity_for_attribute_id(attribute_id)

    def has_post_dependency(self, attribute: CPM_Attribute, aggregated=None):
        return self.__CS.has_post_dependency(attribute, aggregated)

    def get_local_attributes_for_activity_id(self, act_id) -> list[CPM_Attribute]:
        """
        Local attributes are those that are specific for this activity,
        in particular, no standard attributes like timestamps.

        :act_id:
        """
        return [attr for attr in self.get_attributes_for_activity_id(act_id)
                if attr.get_domain_type() not in CPM_Domain_Type.get_independent_domain_types()]

    def get_start_time_attribute_for_activity(self, activity: CPM_Activity):
        return self.__CS.get_start_time_attribute_for_activity(activity)

    def get_complete_time_attribute_for_activity(self, activity: CPM_Activity):
        return self.__CS.get_complete_time_attribute_for_activity(activity)

    def get_selection_functions_smls(self):
        return self.__Sagg.get_smls()

    def get_aggregation_functions_smls(self):
        return self.__Fagg.get_smls()

    def get_selection_function_for_relation(self, r: AttributeRelation):
        return self.__Sagg.relationsToSelection[r]

    def get_aggregation_function_for_relation(self, r: AttributeRelation):
        return self.__Fagg.relationsToAggregation[r]

    def get_all_valuation_parameter_domains(self):
        return self.__V.get_all_valuation_parameter_domains()

    def get_aggregated_relations(self):
        return self.__CS.get_aggregated_relations()

    def get_attributes_at_activity_with_aggregation_postdependency(self, act: CPM_Activity):
        return self.__CS.get_attributes_at_activity_with_aggregation_postdependency(act)

    def get_aggregation_functions(self):
        return list(self.get_aggregation_function().values())

    def get_aggregation_domains(self):
        fagg: AggregationFunction
        domains = []
        for fagg in self.get_aggregation_function().relationsToAggregation.values():
            domains = domains + [fagg.input_domain] if fagg.input_domain not in domains else domains
            domains = domains + [fagg.output_domain] if fagg.output_domain not in domains else domains
        return domains
