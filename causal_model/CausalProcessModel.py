from causal_model.CausalProcessStructure import CausalProcessStructure, AttributeRelation, Attribute
from utils.validators import validate_condition


class StandardMLCode:

    def __init__(self, smltext):
        self.__smltext = smltext

    def get_smltext(self):
        return self.__smltext


class AggregationSelection:

    def __validate(self):
        validate_condition(
            all(isinstance(r, AttributeRelation) for r in self.__relations))
        validate_condition(
            all(isinstance(r, StandardMLCode) for r in self.__selections))

    def __init__(self, relationsToSelection: dict):
        self.__relations = list(relationsToSelection.keys())
        self.__selections = list(relationsToSelection.values())
        self.relationsToSelection = relationsToSelection

    def get_relations(self):
        return self.__relations


class AggregationFunction:

    def __validate(self):
        validate_condition(
            all(isinstance(r, AttributeRelation) for r in self.__relations))
        validate_condition(
            all(isinstance(r, StandardMLCode) for r in self.__aggregations))

    def __init__(self, relationsToAggregation: dict):
        self.__relations = list(relationsToAggregation.keys())
        self.__aggregations = list(relationsToAggregation.values())
        self.relationsToSelection = relationsToAggregation

    def get_relations(self):
        return self.__relations


class AttributeValuation:

    def __validate(self):
        validate_condition(
            all(isinstance(r, Attribute) for r in self.__attributes))
        validate_condition(
            all(isinstance(r, StandardMLCode) for r in self.__valuations))

    def __init__(self, attributeToValuation: dict):
        self.__attributes = list(attributeToValuation.keys())
        self.__valuations = list(attributeToValuation.values())
        self.attributeToValuation = attributeToValuation

    def get_attributes(self):
        return self.__attributes


class CausalProcessModel:

    def __validate(self):
        cs_attributes = self.__CS.get_attributes()
        cs_aggregated_relations = self.__CS.get_aggregated_relations()
        v_attributes = self.__V.get_attributes()
        sagg_relations = self.__Sagg.get_relations()
        fagg_relations = self.__Fagg.get_relations()
        validate_condition(
            all(attr in cs_attributes for attr in v_attributes))
        validate_condition(
            all(r in cs_aggregated_relations for r in sagg_relations))
        validate_condition(
            all(r in cs_aggregated_relations for r in fagg_relations))
        validate_condition(
            all(r in sagg_relations for r in fagg_relations))
        validate_condition(
            all(r in fagg_relations for r in sagg_relations))

    def __init__(self,
                 CS: CausalProcessStructure,
                 Sagg: AggregationSelection,
                 Fagg: AggregationFunction,
                 V: AttributeValuation
                 ):
        self.__CS = CS
        self.__Sagg = Sagg
        self.__Fagg = Fagg
        self.__V = V

    def get_aggregation_selection(self):
        return self.__Sagg

    def get_aggregation_function(self):
        return self.__Fagg

    def get_attribute_valuation(self):
        return self.__V

    def get_activities(self):
        return self.__CS.get_activities()

    def get_activity_names(self):
        activities = self.get_activities()
        activity_names = [act.get_name() for act in activities]
        return activity_names

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

    def add_activity(self, activity_name, activity_id):
        return self.__CS.add_activity(activity_name, activity_id)

    def get_attributes_by_activity_id(self, activity_id):
        self.__CS.get_attributes_by_activity(activity_id)

    def to_string(self):
        s = ""
        s += self.__CS.print()
        return s
