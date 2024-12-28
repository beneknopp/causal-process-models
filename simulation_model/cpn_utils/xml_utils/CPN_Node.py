from simulation_model.cpn_utils.xml_utils.Attributes import Posattr
from simulation_model.cpn_utils.xml_utils.CPN_ID_Manager import CPN_ID_Manager
from simulation_model.cpn_utils.xml_utils.DOM_Element import DOM_Element


class CPN_Node(DOM_Element):

    element_id: str

    def __init__(self, tag: str, cpn_id_manager: CPN_ID_Manager, attributes=None, child_elements=None):
        if attributes is None:
            attributes = dict()
        if child_elements is None:
            child_elements = []
        self.element_id = cpn_id_manager.give_ID()
        attributes["id"] = self.element_id
        DOM_Element.__init__(self, tag, attributes, child_elements)

    def get_id(self) -> str:
        return self.attributes["id"]

    def get_position(self) -> Posattr:
        return list(filter(lambda x: isinstance(x, Posattr), self.child_elements))[0]