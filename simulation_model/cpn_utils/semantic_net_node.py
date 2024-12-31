from simulation_model.cpn_utils.xml_utils.cpn_id_managment import CPN_ID_Manager
from simulation_model.cpn_utils.xml_utils.cpn_node import CPN_Node


class SemanticNetNode(CPN_Node):

    incoming_arcs: []
    outgoing_arcs: []

    def __init__(self, tag: str, cpn_id_manager: CPN_ID_Manager, attributes=None, child_elements=None):
        if attributes is None:
            attributes = dict()
        if child_elements is None:
            child_elements = []
        self.incoming_arcs = []
        self.outgoing_arcs = []
        CPN_Node.__init__(self, tag, cpn_id_manager, attributes, child_elements)

    def add_incoming_arc(self, arc):
        self.incoming_arcs.append(arc)

    def add_outgoing_arc(self, arc):
        self.outgoing_arcs.append(arc)