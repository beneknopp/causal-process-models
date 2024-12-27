from typing import Any

from utils.validators import validate_condition


class Attribute:

    def __init__(self, attr_id, name=None):
        self.attr_id = attr_id
        if name is None:
            self.name = attr_id

    def print(self):
        return self.name

    def get_id(self):
        return self.attr_id


class Activity:

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
        validate_condition(all(attr in self.__amap for attr in self.__attributes))
        validate_condition(all(key in self.__attributes for key in self.__amap))

    def __init__(self, amap: dict):
        self.__attributes = list(amap.keys())
        self.__activities = list(amap.values())
        self.__amap = amap
        self.__validate()

    def get_activity_for_attribute(self, attribute):
        return self.__amap[attribute]

    def get_attributes_for_activity(self, activity):
        return [attr for attr, act in self.__amap.items() if act == activity]

    def get_attributes_for_activity_id(self, activity_id: str):
        return [attr for attr, act in self.__amap.items() if act.get_id() == activity_id]

    def get_attributes(self):
        return self.__attributes

    def get_activities(self):
        return self.__activities


class AttributeRelation:

    def __init__(self, inattr, outattr, is_aggregated):
        self.__inattr: Attribute = inattr
        self.__outattr: Attribute = outattr
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
            all(isinstance(attr, Attribute) for attr in self.__attributes))

    def __validate_activities(self):
        validate_condition(
            all(isinstance(act, Activity) for act in  self.__activities))

    def __validate_attribute_activities(self):
        validate_condition(
            all(attr in self.__attributes
                for attr in self.__attributeActivites.get_attributes()))
        validate_condition(
            all(attr in self.__attributeActivites.get_attributes()
                for attr in self.__attributes)
        )
        validate_condition(
            all(act in self.__activities
                for act in self.__attributeActivites.get_activities()))

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
                    self.__attributeActivites.get_activity_for_attribute(r.get_in()) ==
                    self.__attributeActivites.get_activity_for_attribute(r.get_out())
            ) for r in non_aggregated_relations))

    def __validate(self):
        self.__validate_attributes()
        self.__validate_activities()
        self.__validate_attribute_activities()

    def __init__(self,
                 attributes: list[Attribute],
                 activities: list[Activity],
                 attributeActivites: AttributeActivities,
                 relations: list[AttributeRelation],
                 ):
        self.__attributes = attributes
        self.__activities = activities
        self.__attributeActivites = attributeActivites
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
        return self.__attributeActivites

    def add_activity(self, activity_name, activity_id):
        if activity_id in [act.get_id() for act in self.__activities]:
            raise ValueError("activity with id {0} already exists".format(activity_id))
        if activity_name in [act.get_name() for act in self.__activities]:
            raise ValueError("activity with name {0} already exists".format(activity_name))
        act = Activity(activity_name, activity_id)
        self.__activities.append(act)
        return act

    def get_attributes_by_activity(self, act_id):
        return self.__attributeActivites.get_attributes_for_activity_id(act_id)

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

