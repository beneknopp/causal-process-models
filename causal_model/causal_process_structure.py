from collections import Counter
from enum import Enum

from object_centric.object_type_structure import ObjectType, get_default_object_type
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
        """
        An attribute within a CausalProcessStructure.

        :param attr_domain: The domain (data type) of the attribute
        :param attr_name: the name of the attribute
        :param attr_id: the ID of the attribute
        """
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

    def get_name(self):
        return self.__attr_name


class CPM_Categorical_Attribute(CPM_Attribute):

    def __validate(self):
        validate_condition(all(" " not in l for l in self.__labels),
                           "Labels must not contain whitespaces.")

    def __init__(self, attr_id, labels: list[str]):
        """
        An categorical attribute within a CausalProcessStructure.

        :param attr_id: the ID of the attribute
        :param labels: the labels (values) that this attribute can have
        """
        self.__labels = labels
        super().__init__(CPM_Attribute_Domain.CATEGORICAL, attr_id)
        self.__validate()

    def get_labels(self):
        return self.__labels


class CPM_Activity:

    def __init__(self, act_name, leading_type: ObjectType = None):
        """
        An activity within a CausalProcessStructure.

        :param act_name: the name of the activity
        """
        self.act_name = act_name
        self.act_id = "_".join(act_name.lower().split(" "))
        if leading_type is None:
            leading_type = get_default_object_type()
        self.leading_type = leading_type

    def print(self):
        return self.act_name

    def get_id(self):
        return self.act_id

    def get_name(self):
        return self.act_name

    def get_leading_type(self):
        return self.leading_type


class AttributeActivities:

    def __validate(self):
        validate_condition(all(attr in self.__amap for attr in self.__attribute_ids))
        validate_condition(all(key in self.__attribute_ids for key in self.__amap))

    def __init__(self, amap: dict[str, CPM_Activity]):
        """
        At which activity each attribute within a causal structure is observed.

        :param amap: a dictionary from attribute IDs to Activities
        """
        self.__attribute_ids = list(amap.keys())
        self.__activities = list(amap.values())
        self.__amap = amap
        self.__validate()

    def get_activity_for_attribute_id(self, attribute_id):
        return self.__amap[attribute_id]

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

    def __init__(self, inattr: CPM_Attribute, outattr: CPM_Attribute, is_aggregated: bool = False):
        """
        A causal dependency between two event attributes of the causal model.

        :param inattr: the source of the dependency
        :param outattr: the target of the dependency
        :param is_aggregated: whether this is an aggregated dependency
        """
        self.__inattr = inattr
        self.__outattr = outattr
        self.__is_aggregated = is_aggregated

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
                for attr_id in self.__attributeActivities.get_attribute_ids()),
            "There is an attribute for which an activity is specified, but the attribute is not explicitly listed among the attributes in the causal structure."
        )
        validate_condition(
            all(attr_id in self.__attributeActivities.get_attribute_ids()
                for attr_id in [a.get_id() for a in self.__attributes]),
            "There is an attribute listed among the attributes in the causal structure, but no activity is specified for the attribute."
        )
        validate_condition(
            all(act in self.__activities
                for act in self.__attributeActivities.get_activities()),
            "There is an activity for which an attribute is assigned, but the activity is not explicitly listed among the activities in the causal structure.")

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
                    self.__attributeActivities.get_activity_for_attribute_id(r.get_in().get_id()) ==
                    self.__attributeActivities.get_activity_for_attribute_id(r.get_out().get_id())
            ) for r in non_aggregated_relations),
            "There are non-aggregated causality between attributes at the same events.")

    def __validate(self):
        self.__validate_attributes()
        self.__validate_activities()
        self.__validate_attribute_activities()
        self.__validate_relations()

    def __init__(self,
                 attributes: list[CPM_Attribute],
                 activities: list[CPM_Activity],
                 attributeActivities: AttributeActivities,
                 relations: list[AttributeRelation],
                 ):
        """
        This structure specifies what attributes exist within the process, at what activities they emerge, and between which attributes
        there exist (causal) dependencies.

        :param attributes: the attributes
        :param activities: the activities
        :param attributeActivities: a map from attributes to activities
        :param relations: the dependencies between attributes
        """
        self.__attributes = attributes
        self.__activities = activities
        self.__attributeActivities = attributeActivities
        self.__relations = relations
        self.__validate()

    def get_relations(self):
        return self.__relations

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
        Get all attributes that are the source of a non-aggregated dependency.

        :return: the attributes
        """
        r: AttributeRelation
        non_aggregated_relations = self.get_non_aggregated_relations()
        non_aggregated_attributes = list(set([r.get_in() for r in non_aggregated_relations]))
        return non_aggregated_attributes

    def get_attributes_with_aggregated_dependencies(self):
        """
        Get all attributes that are the source of an aggregated dependency.

        :return: the attributes
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

    def add_activity(self, activity_name):
        act = CPM_Activity(activity_name)
        activity_id = act.act_id
        if activity_id in [act.get_id() for act in self.__activities]:
            raise ValueError("activity with id {0} already exists".format(activity_id))
        if activity_name in [act.get_name() for act in self.__activities]:
            raise ValueError("activity with name {0} already exists".format(activity_name))
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
        s += ("\n\taggregated relations: {0}\n".format(", ".join(
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

    def get_attributes_for_activity_id(self, act_id):
        attr_ids = self.__attributeActivities.get_attribute_ids_for_activity_id(act_id)
        attributes = [attr for attr in self.__attributes if attr.get_id() in attr_ids]
        return attributes

    def has_relation(self,  attr_in_id: str, attr_out_id: str, is_aggregated:bool=None):
        if is_aggregated is not None:
            relations = self.get_aggregated_relations() if is_aggregated else self.get_non_aggregated_relations()
        else:
            relations = self.get_relations()
        r: AttributeRelation
        return any(r.get_in().get_id() == attr_in_id and r.get_out().get_id() == attr_out_id for r in relations)

    def get_activity_for_attribute_id(self, attribute_id):
        return self.__attributeActivities.get_activity_for_attribute_id(attribute_id)
