from object_centric.object_type_structure import ObjectType
from simulation_model.cpn_utils.semantic_net_node import SemanticNetNode
from simulation_model.cpn_utils.xml_utils.attributes import Posattr, Fillattr, Lineattr, Textattr
from simulation_model.cpn_utils.xml_utils.cpn_id_managment import CPN_ID_Manager
from simulation_model.cpn_utils.xml_utils.cpn_node import CPN_Node
from simulation_model.cpn_utils.xml_utils.dom_element import DOM_Element
from simulation_model.cpn_utils.xml_utils.layout import Text, Ellipse
from simulation_model.cpn_utils.xml_utils.semantics import Token, Marking, Type, Initmark, PlaceType
from object_centric.object_centric_petri_net import ObjectCentricPetriNetPlace as OCPN_Place


class Port(CPN_Node):
    __default_x_offset = -25.0
    __default_y_offset = -17.0
    type: str

    def __init__(self, cpn_id_manager: CPN_ID_Manager, ref_x, ref_y, type):
        self.type = type
        tag = "port"
        attributes = dict()
        attributes["type"] = type
        child_elements = []
        x = str(float(ref_x) + self.__default_x_offset)
        y = str(float(ref_y) + self.__default_y_offset)
        child_elements.append(Posattr(x, y))
        child_elements.append(Fillattr("Solid"))
        child_elements.append(Lineattr("0"))
        child_elements.append(Textattr())
        element_id = cpn_id_manager.give_ID()
        CPN_Node.__init__(self, tag, element_id, attributes, child_elements)


class Pageattr(DOM_Element):

    def __init__(self, name):
        tag = "pageattr"
        attributes = dict()
        attributes["name"] = name
        DOM_Element.__init__(self, tag, attributes)


class CPN_Place(SemanticNetNode):
    colset_name: str
    name: str
    x: str
    y: str
    colour_layout: str
    initmark: str
    is_initial: bool
    object_type: ObjectType

    def __init__(self, name, x, y, cpn_id_manager: CPN_ID_Manager, colset_name: str = "UNIT",
                 is_initial: bool = False, initmark: str = None, coordinate_scaling_factor=1.0,
                 fill_colour="White", line_colour="Black", text_colour="Black",
                 object_type: ObjectType = None,
                 ocpn_place: OCPN_Place = None):
        self.cpn_id_manager = cpn_id_manager
        self.colset_name = colset_name
        self.name = name
        self.x = str(coordinate_scaling_factor * float(x))
        self.y = str(coordinate_scaling_factor * float(y))
        self.initmark = initmark
        self.is_initial = is_initial
        self.arcs = []
        if ocpn_place is not None and object_type is not None:
            if ocpn_place.get_object_type() != object_type:
                raise ValueError()
        self.ocpn_place = ocpn_place
        self.object_type = object_type
        tag = "place"
        attributes = dict()
        pos = Posattr(x, y)
        child_elements = []
        child_elements.append(pos)
        child_elements.append(Fillattr("", colour=fill_colour))
        child_elements.append(Lineattr("1", colour=line_colour))
        child_elements.append(Textattr(colour=text_colour))
        child_elements.append(Text(name))
        child_elements.append(Ellipse())
        child_elements.append(Token())
        child_elements.append(Marking())
        child_elements.append(PlaceType(cpn_id_manager, pos, colset_name))
        child_elements.append(Initmark(cpn_id_manager, pos, initmark))
        SemanticNetNode.__init__(self, tag, cpn_id_manager, attributes, child_elements)

    def set_name(self, name: str):
        text_child: Text = list(filter(lambda c: isinstance(c, Text), self.child_elements))[0]
        text_child.set_text(name)
        self.name = name

    def get_ocpn_place(self):
        return self.ocpn_place

    @classmethod
    def fromPlace(cls, place):
        name = place.name
        x = place.x
        y = place.y
        cpn = place.cpn
        colset_name = place.colset_name
        initmark = place.initmark
        is_inital = place.is_initial
        return cls(name, x, y, cpn, colset_name, is_inital, initmark)

    def make_port(self, type, subpage):
        self.add_child(Port(self.cpn_id_manager, self.x, self.y, type))
        # self.add_child(Pageattr(subpage.name))

    def set_initmark_text(self, initmark_text):
        self.initmark = initmark_text
        initmark: Initmark = list(filter(lambda c: isinstance(c, Initmark), self.child_elements))[0]
        initmark.set_text_content(initmark_text)

    def set_colset_name(self, colset_name: str):
        place_type_child: PlaceType = list(filter(lambda c: isinstance(c, PlaceType), self.child_elements))[0]
        place_type_child.set_colset_name(colset_name)
        self.colset_name = colset_name

    def get_name(self):
        return self.name
