from simulation_model.cpn_utils.xml_utils.cpn_id_managment import CPN_ID_Manager
from simulation_model.cpn_utils.xml_utils.cpn_node import CPN_Node
from simulation_model.cpn_utils.xml_utils.dom_element import DOM_Element


class Constraints(DOM_Element):

    def __init__(self):
        tag = "constraints"
        attributes = dict()
        DOM_Element.__init__(self, tag, attributes)


class Pageattr(DOM_Element):

    def __init__(self, name):
        tag = "pageattr"
        attributes = dict()
        attributes["name"] = name
        DOM_Element.__init__(self, tag, attributes)


class Page(CPN_Node):

    name: str
    transitions: []
    places: []

    def __init__(self, name: str, cpn_id_manager: CPN_ID_Manager, places: [] = [], transitions: [] = [],
                 arcs: [] = [], subpage_transition=None):
        self.name = name
        tag = "page"
        self.transitions = []
        self.places = []
        self.subpage_transition = subpage_transition
        attributes = dict()
        child_elements = []
        child_elements.append(Pageattr(name))
        child_elements += places
        child_elements += transitions
        child_elements += arcs
        child_elements.append(Constraints())
        CPN_Node.__init__(self, tag, cpn_id_manager, attributes, child_elements)

    def add_transitions(self, transitions):
        self.child_elements += (transitions)
        self.transitions += (transitions)

    def add_places(self, places):
        self.child_elements += places
        self.places += places

    def get_places(self):
        return self.places

    def get_transitions(self):
        return self.transitions
