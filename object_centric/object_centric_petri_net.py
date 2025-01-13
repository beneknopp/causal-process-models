from object_centric.object_type_structure import ObjectType, get_default_object_type
from process_model.petri_net import SimplePetriNetTransition, SimplePetriNetArc, SimplePetriNetNode, SimplePetriNet, \
    LabelingFunction, SimplePetriNetPlace
from utils.validators import validate_condition


class ObjectCentricPetriNetNode(SimplePetriNetNode):

    def __init__(self, node_id: str, x: float, y: float):
        super().__init__(node_id, x, y)


class ObjectCentricPetriNetPlace(ObjectCentricPetriNetNode, SimplePetriNetPlace):

    def __init__(self, node_id: str, x: float, y: float, object_type: ObjectType = None, is_initial: bool = False, is_final: bool = False):
        if object_type is None:
            object_type = get_default_object_type()
        ObjectCentricPetriNetNode.__init__(self, node_id, x, y)
        SimplePetriNetPlace.__init__(self, node_id, x, y, is_initial=is_initial, is_final=is_final)
        self.__object_type = object_type

    def get_object_type(self):
        return self.__object_type


class ObjectCentricPetriNetTransition(ObjectCentricPetriNetNode, SimplePetriNetTransition):

    def __init__(self, node_id: str, x: float, y: float, leading_type: ObjectType = None):
        if leading_type is None:
            leading_type = get_default_object_type()
        ObjectCentricPetriNetNode.__init__(self, node_id, x, y)
        SimplePetriNetTransition.__init__(self, node_id, x, y)
        self.__leading_type = leading_type

    def get_leading_type(self):
        return self.__leading_type


class ObjectCentricPetriNetArc(SimplePetriNetArc):

    def __init__(self, source: SimplePetriNetNode, target: SimplePetriNetNode, is_variable: bool = False):
        super().__init__(source, target)
        self.__is_variable = is_variable

    def is_variable(self):
        return self.__is_variable


class ObjectCentricPetriNet(SimplePetriNet):

    def __validate(self):
        validate_condition(all(isinstance(p, ObjectCentricPetriNetPlace) for p in self.get_places()))
        validate_condition(all(isinstance(t, ObjectCentricPetriNetTransition) for t in self.get_transitions()))
        validate_condition(all(isinstance(a, ObjectCentricPetriNetArc) for a in self.get_arcs()))

    def __init__(self,
                 places: list[ObjectCentricPetriNetPlace],
                 transitions: list[ObjectCentricPetriNetTransition],
                 arcs: list[ObjectCentricPetriNetArc],
                 labels: LabelingFunction):
        super().__init__(places, transitions, arcs, labels)
        self.__original_transitions = transitions[:]
        self.__validate()

    def get_arcs(self) -> list[ObjectCentricPetriNetArc]:
        """
        Get all arcs in the net.

        :return: The arcs
        """
        return self.arcs

    def add_place(self, p):
        self.places = self.places + [p]

    def add_transition(self, t):
        self.transitions = self.transitions + [t]

    def add_arcs(self, arcs):
        self.arcs = self.arcs + arcs

    def remove_arc(self, arc):
        self.arcs = list(filter(lambda a: a is not arc, self.arcs))

    def get_original_transitions(self, labeled=None):
        ts = self.__original_transitions
        if labeled is None:
            return ts
        if labeled:
            return [t for t in ts if self.get_labels().has_label(t.get_id())]
        return [t for t in ts if not self.get_labels().has_label(t.get_id())]
