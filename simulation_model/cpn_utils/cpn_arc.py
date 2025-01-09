from process_model.petri_net import ArcDirection
from simulation_model.cpn_utils.cpn_place import CPN_Place
from simulation_model.cpn_utils.cpn_transition import CPN_Transition
from simulation_model.cpn_utils.semantic_net_node import SemanticNetNode
from simulation_model.cpn_utils.xml_utils.attributes import Textattr, Lineattr, Fillattr, Posattr, Arrowattr
from simulation_model.cpn_utils.xml_utils.cpn_id_managment import CPN_ID_Manager
from simulation_model.cpn_utils.xml_utils.cpn_node import CPN_Node
from simulation_model.cpn_utils.xml_utils.dom_element import DOM_Element
from simulation_model.cpn_utils.xml_utils.layout import Text
from object_centric.object_centric_petri_net import ObjectCentricPetriNetArc as OCPN_Arc


class Annotation(CPN_Node):

    text_element: Text

    def __init__(self, cpn_id_manager: CPN_ID_Manager, source: SemanticNetNode, target: SemanticNetNode,
                 annotation: str = None, text_colour="Black"):
        tag = "annot"
        self.text_element = Text(annotation)
        attributes = dict()
        child_elements = []
        x = str((float(source.get_position().get_x()) + float(target.get_position().get_x()))/2)
        y = str((float(source.get_position().get_y()) + float(target.get_position().get_y()))/2)
        child_elements.append(Posattr(x,y))
        child_elements.append(Fillattr("Solid"))
        child_elements.append(Lineattr("0"))
        child_elements.append(Textattr(colour=text_colour))
        child_elements.append(self.text_element)
        CPN_Node.__init__(self, tag, cpn_id_manager, attributes, child_elements)

    def set_text(self, text_content):
        self.text_element.set_text(text_content)


class CPN_Arc(CPN_Node):

    __x_default = "0.000000"
    __y_default = "0.000000"
    __order_default = "1"
    placeend: CPN_Place
    transend: CPN_Transition
    isVariableArc: bool
    orientation: ArcDirection
    annotation: Annotation
    cpn_id_manager: CPN_ID_Manager

    def __init__(self, cpn_id_manager: CPN_ID_Manager, source: SemanticNetNode, target: SemanticNetNode,
                 annotation_text: str = "", ocpn_arc: OCPN_Arc = None):
        if source.__class__ == CPN_Place and target.__class__ == CPN_Transition:
            orientation = ArcDirection.P2T
            self.placeend = source
            self.transend = target
        elif source.__class__ == CPN_Transition and target.__class__ == CPN_Place:
            orientation = ArcDirection.T2P
            self.transend = source
            self.placeend = target
        else:
            raise AttributeError("Invalid Arc Configuration: Arcs must run from Places to Transitions or from"
                                 + "Transitions to Places")
        source.add_outgoing_arc(self)
        target.add_incoming_arc(self)
        self.source = source
        self.target = target
        self.annotation_text = annotation_text
        self.annotation = Annotation(cpn_id_manager, source, target, annotation_text)
        self.orientation = orientation
        self.cpn_id_manager = cpn_id_manager
        self.ocpn_arc = ocpn_arc
        tag = "arc"
        attributes = dict()
        child_elements = []
        attributes["orientation"] = orientation.value
        attributes["order"] = self.__order_default
        child_elements.append(Posattr(self.__x_default, self.__y_default))
        child_elements.append(Fillattr(""))
        child_elements.append(Lineattr("1"))
        child_elements.append(Textattr())
        child_elements.append(Arrowattr())
        transend_id = source.get_id() if orientation is ArcDirection.T2P else target.get_id()
        placeend_id = source.get_id() if orientation is ArcDirection.P2T else target.get_id()
        child_elements.append(Transend(transend_id))
        child_elements.append(Placeend(placeend_id))
        child_elements.append(self.annotation)
        CPN_Node.__init__(self, tag, cpn_id_manager, attributes, child_elements)

    def set_transend(self, transition):
        transend: Transend = list(filter(lambda c: isinstance(c, Transend), self.child_elements))[0]
        transend.set_id(transition.get_id())

    def get_place(self) -> CPN_Place:
        return self.placeend

    def get_transition(self) -> CPN_Transition:
        return self.transend

    def get_object_type(self):
        if self.placeend.ocpn_place is None:
            return None
        return self.placeend.ocpn_place.get_object_type()

    @classmethod
    def fromArc(cls, arc, new_place, new_transition):
        orientation = arc.orientation
        isVariableArc = arc.isVariableArc
        annotation = arc.annotation.text_element.text
        source = new_place if orientation is ArcDirection.P2T else new_transition
        target = new_place if orientation is ArcDirection.T2P else new_transition
        return cls(arc.cpn, source, target, annotation)

    def set_annotation(self, annotation_text: str):
        self.annotation_text = annotation_text
        self.annotation.set_text(annotation_text)

    def update_target(self, new_target: SemanticNetNode):
        arc: CPN_Arc
        self.target.incoming_arcs = list(filter(lambda arc: arc.get_id() != self.get_id(), self.target.incoming_arcs))
        new_target.add_incoming_arc(self)
        self.target = new_target


class Transend(DOM_Element):

    def __init__(self, transend_id):
        tag = "transend"
        attributes = dict()
        attributes["idref"] = transend_id
        DOM_Element.__init__(self, tag, attributes)

    def set_id(self, transend_id):
        self.attributes["idref"] = transend_id


class Placeend(DOM_Element):

    def __init__(self, placeend_id):
        tag = "placeend"
        attributes = dict()
        attributes["idref"] = placeend_id
        DOM_Element.__init__(self, tag, attributes)
