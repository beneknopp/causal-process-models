from .cpn_id_managment import CPN_ID_Manager
from .cpn_node import CPN_Node
from .dom_element import DOM_Element
from .layout import Snap, Text
from .attributes import Posattr, Fillattr, Lineattr, Textattr


class Marking(DOM_Element):

    __x_default = "0.000000"
    __y_default = "0.000000"
    __hidden_default = "true"

    def __init__(self):
        tag = "marking"
        attributes = dict()
        children = []
        attributes["x"] = self.__x_default
        attributes["y"] = self.__y_default
        attributes["hidden"] = self.__hidden_default
        children.append(Snap())
        DOM_Element.__init__(self, tag, attributes, children)


class PlaceType(CPN_Node):

    __x_offset_default = 40.0
    __y_offset_default = -20.0

    def __init__(self, cpn_id_manager: CPN_ID_Manager, refpos: Posattr, colset_name: str,
                 colour_layout: str = "Black"):
        tag = "type"
        attributes = dict()
        child_elements = []
        ref_x = refpos.get_x()
        ref_y = refpos.get_y()
        x = str(float(ref_x) + self.__x_offset_default)
        y = str(float(ref_y) + self.__y_offset_default)
        child_elements.append(Posattr(x, y))
        child_elements.append(Fillattr("Solid"))
        child_elements.append(Lineattr("0", colour_layout))
        child_elements.append(Textattr(colour_layout))
        child_elements.append(Text(colset_name))
        CPN_Node.__init__(self, tag, cpn_id_manager, attributes, child_elements)


class Token(DOM_Element):

    __x_default = "-44.000000"
    __y_default = "0.000000"

    def __init__(self):
        tag = "token"
        attributes = dict()
        attributes["x"] = self.__x_default
        attributes["y"] = self.__y_default
        DOM_Element.__init__(self, tag, attributes)


class Type(DOM_Element):

    def __init__(self, cpn_id_manager: CPN_ID_Manager, ref_position: Posattr):
        tag = "text"
        attributes = dict()
        children = []
        element_id = cpn_id_manager.give_ID()
        attributes["id"] = element_id
        x = str(float(ref_position.attributes["x"]) + 30)
        y = str(float(ref_position.attributes["y"]) + 30)
        children.append(Posattr(x, y))
        children.append(Fillattr("Solid"))
        children.append(Lineattr("0"))
        children.append(Textattr())
        child_elements.append(Text(colset_name))
        DOM_Element.__init__(self, tag, attributes, children)


class Initmark(CPN_Node):

    __x_offset_default = 50
    __y_offset_default = 30

    def __init__(self, cpn_id_manager: CPN_ID_Manager, ref_position: Posattr, initmark: str):
        tag = "initmark"
        attributes = dict()
        child_elements = []
        x = str(float(ref_position.attributes["x"]) + self.__x_offset_default)
        y = str(float(ref_position.attributes["y"]) + self.__y_offset_default)
        child_elements.append(Posattr(x, y))
        child_elements.append(Fillattr("Solid"))
        child_elements.append(Lineattr("0"))
        child_elements.append(Textattr())
        child_elements.append(Text(initmark))
        CPN_Node.__init__(self, tag, cpn_id_manager, attributes, child_elements)