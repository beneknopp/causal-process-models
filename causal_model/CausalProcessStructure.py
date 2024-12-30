from collections import Counter
from enum import Enum
from utils.validators import validate_condition


class CPM_Attribute_Domain(Enum):
    """
    An attribute domain is the data type. Currently supported are:
    CATEGORICAL.
    """
    CATEGORICAL = "CATEGORICAL"


class CPM_Attribute:

    def __validate(self):
        validate_condition(" " not in self.__attr_id,
                           "Attribute ID must not contain whitespaces.")

    def __init__(self, attr_domain: CPM_Attribute_Domain, attr_name, attr_id=None):
        self.__attr_domain = attr_domain
        self.__attr_name = attr_name
        if attr_id is None:
            attr_id = "_".join(attr_name.split(" "))
        self.__attr_id = attr_id
        self.__validate()

    def print(self):
        return self.__attr_name

    def get_id(self):
        return self.__attr_id

    def get_domain(self):
        return self.__attr_domain


class CPM_Categorical_Attribute(CPM_Attribute):

    def __validate(self):
        validate_condition(all(" " not in l for l in self.__labels),
                           "Labels must not contain whitespaces.")

    def __init__(self, attr_id, labels: list):
        self.__labels = labels
        super().__init__(CPM_Attribute_Domain.CATEGORICAL, attr_id)
        self.__validate()

    def get_labels(self):
        return self.__labels


class CPM_Activity:

    def __init__(self, attr_id, name=None):
        self.attr_id = attr_id
        if name is None:
            self.name = attr_id

    def print(self):
        return self.name

    def get_id(self):
        return self.attr_id

    def get_name(self):
        return self.name


class AttributeActivities:

    def __validate(self):
        validate_condition(all(attr in self.__amap for attr in self.__attribute_ids))
        validate_condition(all(key in self.__attribute_ids for key in self.__amap))

    def __init__(self, amap: dict):
        self.__attribute_ids = list(amap.keys())
        self.__activities = list(amap.values())
        self.__amap = amap
        self.__validate()

    def get_activity_for_attribute(self, attribute):
        return self.__amap[attribute]

    def get_attributes_for_activity(self, activity):
        return [attr for attr, act in self.__amap.items() if act == activity]

    def get_attribute_ids_for_activity_id(self, activity_id: str):
        return [attr for attr, act in self.__amap.items() if act.get_id() == activity_id]

    def get_attribute_ids(self):
        return self.__attribute_ids

    def get_activities(self):
        return self.__activities

    def get_activity_ids(self):
        return [act.get_id() for act in self.__activities]


class AttributeRelation:

    def __init__(self, inattr, outattr, is_aggregated):
        self.__inattr: CPM_Attribute = inattr
        self.__outattr: CPM_Attribute = outattr
        self.__is_aggregated: bool = is_aggregated

    def get_in(self):
        return self.__inattr

    def get_out(self):
        return self.__outattr

    def is_aggregated(self):
        return self.__is_aggregated

    def print(self):
        return "({0}, {1})".format(
            self.__inattr.print(),
            self.__outattr.print()
        )


class CausalProcessStructure:

    def __validate_attributes(self):
        validate_condition(
            all(isinstance(attr, CPM_Attribute) for attr in self.__attributes))
        # All categorical attributes should have unique (non-intersecting) labels
        attr: CPM_Attribute
        cat_attr: CPM_Categorical_Attribute
        all_labels = [
            cat_attr.get_labels()
            for cat_attr in
            filter(lambda attr: attr.get_domain() == CPM_Attribute_Domain.CATEGORICAL,
                   self.__attributes)
        ]
        all_labels = [element for sublist in all_labels for element in sublist]
        intersecting_labels = [item for item, count in Counter(all_labels).items() if count > 1]
        validate_condition(
            len(intersecting_labels) == 0,
            "There are duplicate labels ({0}) across different categorical attributes.".format(
                intersecting_labels
            )
        )

    def __validate_activities(self):
        validate_condition(
            all(isinstance(act, CPM_Activity) for act in self.__activities))

    def __validate_attribute_activities(self):
        validate_condition(
            all(attr_id in [a.get_id() for a in self.__attributes]
                for attr_id in self.__attributeActivities.get_attribute_ids()))
        validate_condition(
            all(attr_id in self.__attributeActivities.get_attribute_ids()
                for attr_id in [a.get_id() for a in self.__attributes])
        )
        validate_condition(
            all(act in self.__activities
                for act in self.__attributeActivities.get_activities()))

    def __validate_relations(self):
        validate_condition(
            all(isinstance(r, AttributeRelation)
                for r in self.__relations))
        validate_condition(
            all(r.get_in() in self.__attributes
                and r.get_out() in self.__attributes
                for r in self.__relations)
        )
        non_aggregated_relations = self.get_non_aggregated_relations()
        # no non-aggregated causality between attributes at the same events
        validate_condition(
            all(not (
                    self.__attributeActivities.get_activity_for_attribute(r.get_in()) ==
                    self.__attributeActivities.get_activity_for_attribute(r.get_out())
            ) for r in non_aggregated_relations),
            "There are non-aggregated causality between attributes at the same events.")

    def __validate(self):
        self.__validate_attributes()
        self.__validate_activities()
        self.__validate_attribute_activities()

    def __init__(self,
                 attributes: list[CPM_Attribute],
                 activities: list[CPM_Activity],
                 attributeActivities: AttributeActivities,
                 relations: list[AttributeRelation],
                 ):
        self.__attributes = attributes
        self.__activities = activities
        self.__attributeActivities = attributeActivities
        self.__relations = relations
        self.__validate()

    def get_aggregated_relations(self):
        return list(filter(
            lambda r: r.is_aggregated(),
            self.__relations))

    def get_non_aggregated_relations(self):
        return list(filter(
            lambda r: not r.is_aggregated(),
            self.__relations))

    def get_attributes_with_non_aggregated_dependencies(self):
        """
        get all attributes that are the source of a non-aggregated dependency
        """
        r: AttributeRelation
        non_aggregated_relations = self.get_non_aggregated_relations()
        non_aggregated_attributes = [r.get_in() for r in non_aggregated_relations]
        return non_aggregated_attributes

    def get_attributes_with_aggregated_dependencies(self):
        """
        get all attributes that are the source of an aggregated dependency
        """
        r: AttributeRelation
        aggregated_relations = self.get_aggregated_relations()
        aggregated_attributes = [r.get_in() for r in aggregated_relations]
        return aggregated_attributes

    def get_attributes(self):
        return self.__attributes

    def get_activities(self):
        return self.__activities

    def get_attribute_activities(self):
        return self.__attributeActivities

    def add_activity(self, activity_name, activity_id):
        if activity_id in [act.get_id() for act in self.__activities]:
            raise ValueError("activity with id {0} already exists".format(activity_id))
        if activity_name in [act.get_name() for act in self.__activities]:
            raise ValueError("activity with name {0} already exists".format(activity_name))
        act = CPM_Activity(activity_name, activity_id)
        self.__activities.append(act)
        return act

    def print(self):
        s = ""
        s += ("\tattributes: {0}".format(", ".join(
            map(lambda x: x.print(), self.__attributes))))
        s += ("\n\tactivities: {0}".format(", ".join(
            map(lambda x: x.print(), self.__activities))))
        s += ("\n\tnon-aggregated relations: {0}".format(", ".join(
            map(lambda x: x.print(), self.get_non_aggregated_relations()))))
        s += ("\n\taggregated relations: {0}".format(", ".join(
            map(lambda x: x.print(), self.get_aggregated_relations()))))
        return s

    def get_attribute_ids_by_activity_id(self, activity_id):
        return self.__attributeActivities.get_attribute_ids_for_activity_id(activity_id)

    def get_attribute_ids(self):
        return [attr.get_id() for attr in self.__attributes]

    def get_preset(self, attribute_id):
        relations = self.get_non_aggregated_relations()
        r: AttributeRelation
        preset = filter(lambda r: r.get_out().get_id() == attribute_id, relations)
        return list(preset)
