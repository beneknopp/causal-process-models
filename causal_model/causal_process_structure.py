from collections import Counter
from enum import Enum

from object_centric.object_type_structure import ObjectType, get_default_object_type
from utils.validators import validate_condition

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

class CPM_Domain_Type(Enum):
    """
    An attribute domain is the data type. Currently supported are:
    CATEGORICAL
    EVENT_START_TIME
    EVENT_COMPLETE_TIME
    """
    REAL = "REAL"
    CATEGORICAL = "CATEGORICAL"
    EVENT_START_TIME = "EVENT_START_TIME"
    EVENT_COMPLETE_TIME = "EVENT_COMPLETE_TIME"

    @classmethod
    def get_independent_domain_types(cls):
        """
        Causal effects on these domains cannot be modeled directly.
        For example, event timestamps depend on the control-flow dynamics, process start time, availability calendars etc.
        Thus, to reduce complexity, we do not allow to specify valuation functions for these attributes.

        :return: the independent domains
        """
        return [
            cls.EVENT_START_TIME,
            cls.EVENT_COMPLETE_TIME
        ]

    @classmethod
    def get_timing_domain_types(cls):
        return [
            cls.EVENT_START_TIME,
            cls.EVENT_COMPLETE_TIME
        ]


class CPM_Domain:

    def __init__(self, domain_type: CPM_Domain_Type, domain_id: str):
        self.domain_type = domain_type
        self.__domain_id = domain_id

    def get_id(self):
        return self.__domain_id


class CPM_Categorical_Domain(CPM_Domain):

    def __init__(self, labels: list[str], domain_id: str):
        super().__init__(CPM_Domain_Type.CATEGORICAL, domain_id)
        self.__labels = labels

    def __validate(self):
        validate_condition(all(" " not in l for l in self.__labels),
                           "Labels must not contain whitespaces.")

    def get_labels(self):
        return self.__labels


class CPM_EventStartTime_Domain(CPM_Domain):

    def __init__(self):
        domain_id = "START_TIME_DOM"
        super().__init__(CPM_Domain_Type.EVENT_START_TIME, domain_id)


class CPM_EventCompleteTime_Domain(CPM_Domain):

    def __init__(self):
        domain_id = "END_TIME_DOM"
        super().__init__(CPM_Domain_Type.EVENT_COMPLETE_TIME, domain_id)


class CPM_Real_Domain(CPM_Domain):

    def __init__(self):
        super().__init__(CPM_Domain_Type.REAL, "REAL")


EVENT_START_TIME_DOMAIN = CPM_EventStartTime_Domain()
EVENT_COMPLETE_TIME_DOMAIN = CPM_EventCompleteTime_Domain()
REAL_DOMAIN = CPM_Real_Domain()


class CPM_Attribute:

    activity: CPM_Activity

    def __validate(self):
        validate_condition(" " not in self.__attr_id,
                           "Attribute ID must not contain whitespaces.")

    def __init__(self, attr_domain: CPM_Domain, attr_name, attr_id=None):
        """
        An attribute within a CausalProcessStructure.

        :param attr_domain: The domain (data type) of the attribute
        :param attr_name: the name of the attribute
        :param attr_id: the ID of the attribute
        """
        self.attr_domain = attr_domain
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
        return self.attr_domain

    def get_domain_type(self):
        return self.attr_domain.domain_type

    def get_name(self):
        return self.__attr_name

    def get_activity(self):
        return self.activity

    @classmethod
    def init_domain_attribute(cls, activity_id, domain: CPM_Domain_Type):
        if domain is CPM_Domain_Type.EVENT_START_TIME:
            return CPM_EventStartTime_Attribute(activity_id)
        if domain is CPM_Domain_Type.EVENT_COMPLETE_TIME:
            return CPM_EventCompleteTime_Attribute(activity_id)
        raise ValueError("Invalid domain {0}".format(domain.value))


class CPM_Categorical_Attribute(CPM_Attribute):

    def __init__(self, attr_domain: CPM_Categorical_Domain, attr_name):
        super().__init__(attr_domain, attr_name)

    def get_labels(self):
        return self.attr_domain.get_labels()


class CPM_CaseAttribute(CPM_Attribute):

    def __init__(self, attr_domain: CPM_Domain_Type, attr_name):
        super().__init__(attr_domain, attr_name)


class CPM_EventStartTime_Attribute(CPM_Attribute):

    def __init__(self, activity_id):
        """
        Add a designated start timestamp attribute.

        :param activity_id: The ID of the activity to which this attribute belongs.
        """
        super().__init__(EVENT_START_TIME_DOMAIN,
                         "timestamp_start_" + activity_id)


class CPM_EventCompleteTime_Attribute(CPM_Attribute):

    def __init__(self, activity_id):
        """
        Add a designated completion timestamp attribute.

        :param activity_id: The ID of the activity to which this attribute belongs.
        """
        super().__init__(EVENT_COMPLETE_TIME_DOMAIN,
                         "timestamp_complete_" + activity_id)





class AttributeActivities:

    def __validate(self):
        pass

    def __init__(self, amap: dict[CPM_Attribute, CPM_Activity]):
        """
        At which activity each attribute within a causal structure is observed.

        :param amap: a dictionary from attribute IDs to Activities
        """
        self.__attributes = list(amap.keys())
        self.__attribute_ids = list([k.get_id() for k in amap.keys()])
        self.__attributes_by_ids = {attr.get_id(): attr for attr in self.__attributes}
        self.__activities = list(amap.values())
        self.__amap = amap
        self.__validate()

    def get_activity_for_attribute_id(self, attribute_id):
        attribute = self.__attributes_by_ids[attribute_id]
        return self.__amap[attribute]

    def get_attributes_for_activity(self, activity):
        return [attr for attr, act in self.__amap.items() if act == activity]

    def get_attribute_ids_for_activity_id(self, activity_id: str):
        return [attr.get_id() for attr, act in self.__amap.items() if act.get_id() == activity_id]

    def get_attribute_ids(self):
        return self.__attribute_ids

    def get_activities(self):
        return self.__activities

    def get_activity_ids(self):
        return [act.get_id() for act in self.__activities]

    def add(self, attribute: CPM_Attribute, activity: CPM_Activity, append=False):
        if attribute in self.__attributes:
            return
        self.__amap[attribute] = activity
        if append:
            self.__attributes = self.__attributes + [attribute]
            self.__attribute_ids = self.__attribute_ids + [attribute.get_id()]
        else:
            self.__attributes = [attribute] + self.__attributes
            self.__attribute_ids = [attribute.get_id()] + self.__attribute_ids
            self.__amap = {
                attribute: self.__amap[attribute] for attribute in self.__attributes
            }
        self.__attributes_by_ids[attribute.get_id()] = attribute
        self.__activities = list(set(self.__activities + [activity]))

    def get_complete_time_attribute_for_activity(self, activity):
        all_attrs = self.get_attributes_for_activity(activity)
        complete_time_attribute = list(
            filter(lambda a: a.get_domain_type() is CPM_Domain_Type.EVENT_COMPLETE_TIME,
                   all_attrs))
        if not len(complete_time_attribute) == 1:
            raise ValueError()
        return complete_time_attribute[0]

    def get_start_time_attribute_for_activity(self, activity):
        all_attrs = self.get_attributes_for_activity(activity)
        start_time_attribute = list(filter(lambda a: a.get_domain_type() is CPM_Domain_Type.EVENT_START_TIME,
                                           all_attrs))
        if not len(start_time_attribute) == 1:
            raise ValueError()
        return start_time_attribute[0]


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

    def get_name(self):
        return "{0}{1}{2}".format(
            self.__inattr.get_id(),
            "_agg_" if self.is_aggregated() else "_",
            self.__outattr.get_id()
        )


class CausalProcessStructure:

    def __validate_attributes(self):
        attributes = self.__event_attributes + self.__case_attributes
        validate_condition(
            all(isinstance(attr, CPM_Attribute) for attr in attributes))
        # All categorical attributes should have unique (non-intersecting) labels
        attr: CPM_Attribute
        cat_attr: CPM_Categorical_Attribute
        all_labels = [
            cat_attr.get_labels()
            for cat_attr in
            filter(lambda attr: attr.get_domain_type() == CPM_Domain_Type.CATEGORICAL,
                   attributes)
        ]
        all_labels = [element for sublist in all_labels for element in sublist]
        intersecting_labels = [item for item, count in Counter(all_labels).items() if count > 1]
        validate_condition(
            len(intersecting_labels) == 0,
            "There are duplicate labels ({0}) across different categorical attributes.".format(
                intersecting_labels))
        for domain_type in [CPM_Domain_Type.EVENT_START_TIME, CPM_Domain_Type.EVENT_COMPLETE_TIME]:
            customized_domain_attributes = [attr for attr in attributes if attr.get_domain_type() is domain_type]
            validate_condition(
                len(customized_domain_attributes) <= 1,
                "Event attributes of domain/type '{0}' may be specified at most 1 time per activity".format(
                    domain_type.value))

    def __validate_activities(self):
        validate_condition(
            all(isinstance(act, CPM_Activity) for act in self.__activities))

    def __validate_attribute_activities(self):
        validate_condition(
            all(attr_id in [a.get_id() for a in self.__event_attributes]
                for attr_id in self.__attributeActivities.get_attribute_ids()),
            "There is an event attribute for which an activity is specified, but the attribute is not explicitly "
            "listed among the attributes in the causal structure. "
        )
        validate_condition(
            all(attr_id in self.__attributeActivities.get_attribute_ids()
                for attr_id in [a.get_id() for a in self.__event_attributes]),
            "There is an attribute listed among the event attributes in the causal structure, but no activity is "
            "specified for the attribute. "
        )
        validate_condition(
            all(act in self.__activities
                for act in self.__attributeActivities.get_activities()),
            "There is an activity for which an event attribute is assigned, but the activity is not explicitly listed "
            "among the activities in the causal structure.")

    def __validate_relations(self):
        attributes = self.__event_attributes + self.__case_attributes
        validate_condition(
            all(isinstance(r, AttributeRelation)
                for r in self.__relations))
        validate_condition(
            all(r.get_in() in attributes
                and r.get_out() in attributes
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
                 event_attributes: list[CPM_Attribute],
                 case_attributes: list[CPM_Attribute],
                 activities: list[CPM_Activity],
                 attributeActivities: AttributeActivities,
                 relations: list[AttributeRelation],
                 ):
        """
        This structure specifies what attributes exist within the process, at what activities they emerge, and between which attributes
        there exist (causal) dependencies.

        :param event_attributes: the event attributes
        :param case_attributes: the case attributes
        :param activities: the activities
        :param attributeActivities: a map from attributes to activities
        :param relations: the dependencies between attributes
        """
        self.__event_attributes = event_attributes
        self.__case_attributes = case_attributes
        self.__activities = activities
        self.__attributeActivities = attributeActivities
        self.__relations = relations
        self.__validate()
        self.__expand_with_standard_attributes()
        # TODO: factor out the dictionary and just include activities as attribute member variables
        self.__add_activities_to_attributes()

    def __expand_with_standard_attributes(self):
        for activity in self.__activities:
            for domain_type in [CPM_Domain_Type.EVENT_COMPLETE_TIME,
                                CPM_Domain_Type.EVENT_START_TIME]:
                activity_attributes = self.__attributeActivities.get_attributes_for_activity(activity)
                if not any(attr.get_domain_type() is domain_type for attr in activity_attributes):
                    domain_attribute = CPM_Attribute.init_domain_attribute(activity.get_id(), domain_type)
                    self.__event_attributes = [domain_attribute] + self.__event_attributes
                    self.__attributeActivities.add(domain_attribute, activity)

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
        return self.__case_attributes + self.__event_attributes

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
            map(lambda x: x.print(), self.get_attributes()))))
        s += ("\n\tactivities: {0}".format(", ".join(
            map(lambda x: x.print(), self.__activities))))
        s += ("\n\tnon-aggregated relations: {0}".format(", ".join(
            map(lambda x: x.print(), self.get_non_aggregated_relations()))))
        s += ("\n\taggregated relations: {0}\n".format(", ".join(
            map(lambda x: x.print(), self.get_aggregated_relations()))))
        return s

    def get_attribute_ids_by_activity_id(self, activity_id):
        return self.__attributeActivities.get_attribute_ids_for_activity_id(activity_id)

    def get_event_attribute_ids(self):
        return [attr.get_id() for attr in self.__event_attributes]

    def get_preset(self, attribute: CPM_Attribute, aggregated=None):
        if aggregated is None:
            relations = self.get_relations()
        elif aggregated:
            relations = self.get_aggregated_relations()
        else:
            relations = self.get_non_aggregated_relations()
        r: AttributeRelation
        preset = filter(lambda r: r.get_out() == attribute, relations)
        return list(preset)

    def get_postset(self, attribute: CPM_Attribute, aggregated=None):
        if aggregated is None:
            relations = self.get_relations()
        elif aggregated:
            relations = self.get_aggregated_relations()
        else:
            relations = self.get_non_aggregated_relations()
        r: AttributeRelation
        postset = filter(lambda r: r.get_in().get_id() == attribute.get_id(), relations)
        return list(postset)

    def get_attributes_for_activity_id(self, act_id):
        attr_ids = self.__attributeActivities.get_attribute_ids_for_activity_id(act_id)
        attributes = [attr for attr in self.__event_attributes if attr.get_id() in attr_ids]
        return attributes

    def has_relation(self, attr_in_id: str, attr_out_id: str, is_aggregated: bool = None):
        if is_aggregated is not None:
            relations = self.get_aggregated_relations() if is_aggregated else self.get_non_aggregated_relations()
        else:
            relations = self.get_relations()
        r: AttributeRelation
        return any(r.get_in().get_id() == attr_in_id and r.get_out().get_id() == attr_out_id for r in relations)

    def get_activity_for_attribute_id(self, attribute_id):
        return self.__attributeActivities.get_activity_for_attribute_id(attribute_id)

    def get_attribute_ids(self):
        return [a.get_id() for a in self.__event_attributes + self.__case_attributes]

    def has_post_dependency(self, attribute: CPM_Attribute, aggregated=None):
        return len(self.get_postset(attribute, aggregated)) > 0

    def get_start_time_attribute_for_activity(self, activity):
        return self.__attributeActivities.get_start_time_attribute_for_activity(activity)

    def get_complete_time_attribute_for_activity(self, activity):
        return self.__attributeActivities.get_complete_time_attribute_for_activity(activity)

    def __add_activities_to_attributes(self):
        for attribute in self.__event_attributes:
            act = self.__attributeActivities.get_activity_for_attribute_id(attribute.get_id())
            attribute.activity = act

    def get_attributes_at_activity_with_aggregation_postdependency(self, activity: CPM_Activity):
        aggregated_relations = self.get_aggregated_relations()
        local_aggregated_relations = list(filter(lambda r: r.get_in().activity == activity, aggregated_relations))
        return local_aggregated_relations

