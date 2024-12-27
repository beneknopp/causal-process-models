from utils.validators import validate_condition


class Node:

    def __init__(self, node_id: str):
        self.__node_id = node_id

    def get_id(self):
        return self.__node_id

    def to_string(self):
        return self.__node_id


class Place(Node):

    def __init__(self, node_id: str):
        super().__init__(node_id)


class Transition(Node):

    def __init__(self, node_id: str):
        super().__init__(node_id)


class Arc:

    def __validate(self):
        validate_condition(
            (isinstance(self.__source, Place) and isinstance(self.__target, Transition))
            or
            (isinstance(self.__source, Transition) and isinstance(self.__target, Place))
        )

    def __init__(self, source: Node, target: Node):
        self.__source = source
        self.__target = target

    def to_string(self):
        return ("({0}, {1})".format(
            self.__source.to_string(), self.__target.to_string()
        ))


class LabelingFunction:

    def __init__(self, lmap: dict):
        self.__lmap = lmap

    def get_label(self, transition_id: str):
        return self.__lmap[transition_id]

    def get_keys(self):
        return list(self.__lmap.keys())

    def get_labels(self):
        return list(self.__lmap.values())


class PetriNet:

    def __validate(self):
        validate_condition(
            all(isinstance(p, Place) for p in self.__places))
        validate_condition(
            all(isinstance(p, Transition) for p in self.__transitions))
        validate_condition(
            all(isinstance(p, Arc) for p in self.__arcs))
        transition_ids = map(lambda t: t.get_id(), self.__transitions)
        validate_condition(
            all(t in transition_ids for t in self.__labels.get_keys()))

    def __init__(self,
                 places: list[Place],
                 transitions: list[Transition],
                 arcs: list[Arc],
                 labels: LabelingFunction):
        self.__places = places
        self.__transitions = transitions
        self.__arcs = arcs
        self.__labels = labels
        self.__validate()

    def get_activities(self):
        return list(self.__labels.get_labels())

    def to_string(self):
        s = ""
        s += (
            "\tplaces: {0}".format(", ".join(
                map(lambda x: x.to_string(), self.__places)))
        )
        s += (
            "\n\ttransitions: {0}".format(", ".join(
                map(lambda x: x.to_string(), self.__transitions)))
        )
        s += (
            "\n\tarcs: {0}".format(", ".join(
                map(lambda x: x.to_string(), self.__arcs)))
        )
        return s
