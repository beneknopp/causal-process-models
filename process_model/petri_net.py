from utils.validators import validate_condition


class SimplePetriNetNode:

    def __init__(self, node_id: str, x: float, y: float):
        """
        A place or a transition.

        :param node_id: The unique ID of the node within the net
        :param x: x-coordinate of a visual representation of the net
        :param y: y-coordinate of a visual representation of the net
        """
        self.__node_id = node_id
        self.x = x
        self.y = y

    def get_id(self):
        return self.__node_id

    def to_string(self):
        return self.__node_id


class SimplePetriNetPlace(SimplePetriNetNode):

    def __init__(self, node_id: str, x: float, y: float, is_initial: bool = False):
        self.is_initial = is_initial
        super().__init__(node_id, x, y)


class SimplePetriNetTransition(SimplePetriNetNode):

    def __init__(self, node_id: str, x: float, y: float):
        super().__init__(node_id, x, y)


class SimplePetriNetArc:

    def __validate(self):
        validate_condition(
            (isinstance(self.__source, SimplePetriNetPlace) and isinstance(self.__target, SimplePetriNetTransition))
            or
            (isinstance(self.__source, SimplePetriNetTransition) and isinstance(self.__target, SimplePetriNetPlace))
        )

    def __init__(self, source: SimplePetriNetNode, target: SimplePetriNetNode):
        """
        An objects that connects two SimplePetriNetNodes.

        :param source: The source node
        :param target: The target node
        """
        self.__source = source
        self.__target = target
        self.__id = str(id(self))[:]

    def to_string(self):
        return ("({0}, {1})".format(
            self.__source.to_string(), self.__target.to_string()
        ))

    def get_place(self):
        if isinstance(self.__source, SimplePetriNetPlace):
            return self.__source
        return self.__target

    def get_transition(self):
        if isinstance(self.__source, SimplePetriNetTransition):
            return self.__source
        return self.__target

    def get_source(self):
        return self.__source

    def get_target(self):
        return self.__target

    def get_direction(self):
        if isinstance(self.__source, SimplePetriNetPlace):
            return "PtoT"
        return "TtoP"

    def get_id(self):
        return self.__id


class LabelingFunction:

    def __init__(self, lmap: dict[str, str]):
        """
        Maps a transition ID to the label of that transition.

        :param lmap: The map (dictionary)
        """
        self.__lmap = lmap

    def get_label(self, transition_id: str):
        return self.__lmap[transition_id]

    def get_keys(self):
        return list(self.__lmap.keys())

    def get_labels(self):
        return list(self.__lmap.values())


class SimplePetriNet:

    def __validate(self):
        validate_condition(
            all(isinstance(p, SimplePetriNetPlace) for p in self.__places))
        validate_condition(
            all(isinstance(p, SimplePetriNetTransition) for p in self.__transitions))
        validate_condition(
            all(isinstance(p, SimplePetriNetArc) for p in self.__arcs))
        transition_ids = map(lambda t: t.get_id(), self.__transitions)
        validate_condition(
            all(t in transition_ids for t in self.__labels.get_keys()))

    def __init__(self,
                 places: list[SimplePetriNetPlace],
                 transitions: list[SimplePetriNetTransition],
                 arcs: list[SimplePetriNetArc],
                 labels: LabelingFunction):
        """
        Create a simple labeled Petri net

        :param places: The places
        :param transitions: The transitions
        :param arcs: The arcs
        :param labels: The labels of the labeled transitions
        """
        self.__places = places
        self.__transitions = transitions
        self.__arcs = arcs
        self.__labels = labels
        self.__validate()

    def get_activities(self):
        """
        Get the set of all labels over all transitions in the net.

        :return: The activities (transition labels)
        """
        return list(self.__labels.get_labels())

    def get_places(self):
        """
        Get all places in the net.

        :return: The places
        """
        return self.__places

    def get_transitions(self):
        """
        Get all transitions in the net.

        :return: The transitions
        """
        return self.__transitions

    def get_arcs(self):
        """
        Get all arcs in the net.

        :return: The arcs
        """
        return self.__arcs

    def get_labels(self):
        return self.__labels

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

    def get_transitions_with_label(self, label: str):
        """
        Get all transitions in the Petri net that have a specific label.

        :param label: The label
        :return: The transitions
        """
        t: SimplePetriNetTransition
        transitions_with_label = list(filter(
            lambda t: label == self.__labels.get_label(transition_id=t.get_id()),
            self.__transitions))
        return transitions_with_label

    def get_incoming_arcs(self, node_id: str):
        """
        Get all arcs incoming to a node of the net.

        :param node_id: The id of the SimplePetriNetNode
        :return: The arcs
        """
        a: SimplePetriNetArc
        incoming_arcs = [a for a in self.__arcs if a.get_target().get_id() == node_id]
        return incoming_arcs
