from simulation_model.cpn_utils.CPN_Place import CPN_Place
from simulation_model.cpn_utils.CPN_Transition import CPN_Transition
from simulation_model.cpn_utils.SemanticNetNode import SemanticNetNode
from simulation_model.cpn_utils.xml_utils.Attributes import Textattr, Lineattr, Fillattr, Posattr, Arrowattr
from simulation_model.cpn_utils.xml_utils.CPN_ID_Manager import CPN_ID_Manager
from simulation_model.cpn_utils.xml_utils.CPN_Node import CPN_Node
from simulation_model.cpn_utils.xml_utils.DOM_Element import DOM_Element
from simulation_model.cpn_utils.xml_utils.Layout import Text


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
    orientation: str
    annotation: Annotation
    cpn_id_manager: CPN_ID_Manager

    def __init__(self, cpn_id_manager: CPN_ID_Manager, source: SemanticNetNode, target: SemanticNetNode,
                 annotation_text: str = ""):
        if source.__class__ == CPN_Place and target.__class__ == CPN_Transition:
            orientation = "PtoT"
            self.placeend = source
            self.transend = target
        elif source.__class__ == CPN_Transition and target.__class__ == CPN_Place:
            orientation = "TtoP"
            self.transend = source
            self.placeend = target
        else:
            raise AttributeError("Invalid Arc Configuration: Arcs must run from Places to Transitions or from"
                                 + "Transitions to Places")
        source.add_outgoing_arc(self)
        target.add_incoming_arc(self)
        self.annotation_text = annotation_text
        self.annotation = Annotation(cpn_id_manager, source, target, annotation_text)
        self.orientation = orientation
        self.cpn_id_manager = cpn_id_manager
        tag = "arc"
        attributes = dict()
        child_elements = []
        attributes["orientation"] = orientation
        attributes["order"] = self.__order_default
        child_elements.append(Posattr(self.__x_default, self.__y_default))
        child_elements.append(Fillattr(""))
        child_elements.append(Lineattr("1"))
        child_elements.append(Textattr())
        child_elements.append(Arrowattr())
        transend_id = source.get_id() if orientation == "TtoP" else target.get_id()
        placeend_id = source.get_id() if orientation == "PtoT" else target.get_id()
        child_elements.append(Transend(transend_id))
        child_elements.append(Placeend(placeend_id))
        child_elements.append(self.annotation)
        CPN_Node.__init__(self, tag, cpn_id_manager, attributes, child_elements)

    def set_transend(self, transition):
        transend: Transend = list(filter(lambda c: isinstance(c, Transend), self.child_elements))[0]
        transend.set_id(transition.get_id())

    @classmethod
    def fromArc(cls, arc, new_place, new_transition):
        orientation = arc.orientation
        isVariableArc = arc.isVariableArc
        annotation = arc.annotation.text_element.text
        source = new_place if orientation == "PtoT" else new_transition
        target = new_place if orientation == "TtoP" else new_transition
        return cls(arc.cpn, source, target, annotation)

    def set_annotation(self, annotation_text: str):
        self.annotation_text = annotation_text
        self.annotation.set_text(annotation_text)


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
