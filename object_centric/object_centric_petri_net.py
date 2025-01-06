from object_centric.object_type_structure import ObjectType
from process_model.petri_net import SimplePetriNetTransition, SimplePetriNetArc, SimplePetriNetNode, SimplePetriNet, \
    LabelingFunction, SimplePetriNetPlace
from utils.validators import validate_condition


class ObjectCentricPetriNetNode(SimplePetriNetNode):

    def __init__(self, node_id: str, x: float, y: float):
        super().__init__(node_id, x, y)


class ObjectCentricPetriNetPlace(ObjectCentricPetriNetNode, SimplePetriNetPlace):

    def __init__(self, node_id: str, x: float, y: float, object_type: ObjectType, is_initial: bool = False):
        ObjectCentricPetriNetNode.__init__(self, node_id, x, y)
        SimplePetriNetPlace.__init__(self, node_id, x, y, is_initial=is_initial)
        self.__object_type = object_type

    def get_object_type(self):
        return self.__object_type


class ObjectCentricPetriNetTransition(ObjectCentricPetriNetNode, SimplePetriNetTransition):

    def __init__(self, node_id: str, x: float, y: float, leading_type: ObjectType):
        super().__init__(node_id, x, y)
        self.__object_type = leading_type

    def get_object_type(self):
        return self.__object_type


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

    def __init__(self, places: list[ObjectCentricPetriNetPlace], transitions: list[ObjectCentricPetriNetTransition],
                 arcs: list[ObjectCentricPetriNetArc], labels: LabelingFunction):
        super().__init__(places, transitions, arcs, labels)
        self.__validate()
