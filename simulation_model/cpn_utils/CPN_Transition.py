from enum import Enum

from simulation_model.cpn_utils.SemanticNetNode import SemanticNetNode
from simulation_model.cpn_utils.xml_utils.Attributes import Posattr, Lineattr, Textattr, Fillattr
from simulation_model.cpn_utils.xml_utils.CPN_ID_Manager import CPN_ID_Manager
from simulation_model.cpn_utils.xml_utils.CPN_Node import CPN_Node
from simulation_model.cpn_utils.xml_utils.DOM_Element import DOM_Element
from simulation_model.cpn_utils.xml_utils.Layout import Text, Box


class TransitionType(Enum):
    SILENT = "SILENT"
    ACTIVITY = "ACTIVITY"


class Binding(DOM_Element):
    __x_default = "7.200000"
    __y_default = "-3.000000"

    def __init__(self):
        tag = "binding"
        attributes = dict()
        attributes["x"] = self.__x_default
        attributes["y"] = self.__y_default
        DOM_Element.__init__(self, tag, attributes)


class Guard(CPN_Node):
    __x_offset_default = -39
    __y_offset_default = 31

    def __init__(self, ref_x: str, ref_y: str, cpn_id_manager: CPN_ID_Manager, condition: str = None):
        tag = "cond"
        attributes = dict()
        child_elements = []
        x = str(float(ref_x) + self.__x_offset_default)
        y = str(float(ref_y) + self.__y_offset_default)
        child_elements.append(Posattr(x, y))
        child_elements.append(Fillattr("Solid"))
        child_elements.append(Lineattr("0"))
        child_elements.append(Textattr())
        child_elements.append(Text(condition))
        CPN_Node.__init__(self, tag, cpn_id_manager, attributes, child_elements)

    def set_text_content(self, text):
        text_element: Text = list(filter(lambda c: isinstance(c, Text), self.child_elements))[0]
        text_element.set_text(text)


class Time(CPN_Node):
    __x_offset_default = 24.5
    __y_offset_default = 24.5

    def __init__(self, ref_x: str, ref_y: str, cpn_id_manager: CPN_ID_Manager, delay: str = None):
        tag = "time"
        attributes = dict()
        child_elements = []
        x = str(float(ref_x) + self.__x_offset_default)
        y = str(float(ref_y) + self.__y_offset_default)
        text_element = Text(delay)
        self.text_element = text_element
        child_elements.append(Posattr(x, y))
        child_elements.append(Fillattr("Solid"))
        child_elements.append(Lineattr("0"))
        child_elements.append(Textattr())
        child_elements.append(text_element)
        CPN_Node.__init__(self, tag, cpn_id_manager, attributes, child_elements)


class Code(CPN_Node):
    __x_offset_default = 34.5
    __y_offset_default = -32.0
    text_element: Text

    def __init__(self, ref_x: str, ref_y: str, cpn_id_manager: CPN_ID_Manager, code: str = None, text_colour="Black"):
        tag = "code"
        attributes = dict()
        child_elements = []
        x = str(float(ref_x) + self.__x_offset_default)
        y = str(float(ref_y) + self.__y_offset_default)
        text_element = Text(code)
        self.text_element = text_element
        child_elements.append(Posattr(x, y))
        child_elements.append(Fillattr("Solid"))
        child_elements.append(Lineattr("0"))
        child_elements.append(Textattr(colour=text_colour))
        child_elements.append(text_element)
        CPN_Node.__init__(self, tag, cpn_id_manager, attributes, child_elements)


class Priority(CPN_Node):
    __x_offset_default = -68.0
    __y_offset_default = -15.0

    def __init__(self, ref_x: str, ref_y: str, cpn_id_manager: CPN_ID_Manager, priority: str = None):
        tag = "priority"
        attributes = dict()
        child_elements = []
        x = str(float(ref_x) + self.__x_offset_default)
        y = str(float(ref_y) + self.__y_offset_default)
        child_elements.append(Posattr(x, y))
        child_elements.append(Fillattr("Solid"))
        child_elements.append(Lineattr("0"))
        child_elements.append(Textattr())
        child_elements.append(Text(priority))
        CPN_Node.__init__(self, tag, cpn_id_manager, attributes, child_elements)


# Place Annotations
class Type(CPN_Node):
    __x_offset_default = 40.0
    __y_offset_default = -20.0

    def __init__(self, ref_x: str, ref_y: str, cpn_id_manager: CPN_ID_Manager,
                 colset_name: str, colour_layout: str = "Black"):
        tag = "type"
        attributes = dict()
        child_elements = []
        x = str(float(ref_x) + self.__x_offset_default)
        y = str(float(ref_y) + self.__y_offset_default)
        child_elements.append(Posattr(x, y))
        child_elements.append(Fillattr("Solid"))
        child_elements.append(Lineattr("0", colour_layout))
        child_elements.append(Textattr(colour_layout))
        child_elements.append(Text(colset_name))
        CPN_Node.__init__(self, tag, cpn_id_manager, attributes, child_elements)

    def set_text(self, text):
        text_child: Text = list(filter(lambda c: isinstance(c, Text), self.child_elements))[0]
        text_child.set_text(text)


class Substitution(DOM_Element):

    def __init__(self, ref_x, ref_y, cpn_id_manager: CPN_ID_Manager, subpage_description,
                 subpage_id, portsock_info):
        tag = "subst"
        attributes = dict()
        attributes["subpage"] = subpage_id
        attributes["portsock"] = portsock_info
        child_elements = [SubpageInfo(ref_x, ref_y, cpn_id_manager, subpage_description)]
        DOM_Element.__init__(self, tag, attributes, child_elements)


class SubpageInfo(CPN_Node):
    __default_x_offset = 0
    __default_y_offset = -24.0

    def __init__(self, ref_x, ref_y, cpn_id_manager, subpage_description):
        tag = "subpageinfo"
        attributes = dict()
        attributes["id"] = cpn_id_manager.give_ID()
        attributes["name"] = subpage_description
        child_elements = []
        x = str(float(ref_x) + self.__default_x_offset)
        y = str(float(ref_y) + self.__default_y_offset)
        child_elements.append(Posattr(x, y))
        child_elements.append(Fillattr("Solid"))
        child_elements.append(Lineattr("0"))
        child_elements.append(Textattr())
        CPN_Node.__init__(self, tag, cpn_id_manager, attributes, child_elements)


class RoutingGuard:
    name: str
    x: str
    y: str
    awaited_activities: dict
    awaited_objects: dict
    df_activities: set

    def __init__(self, name: str, x: str, y: str):
        self.name = name
        self.x = x
        self.y = y
        self.awaited_activities = dict()
        self.awaited_objects = dict()
        self.df_activities = set()

    def add_awaited_activities(self, activity_leading_types, awaited_activities):
        for activity in awaited_activities:
            leading_type = activity_leading_types[activity]
            if not leading_type in self.awaited_activities:
                self.awaited_activities[leading_type] = set()
                self.awaited_objects[leading_type] = 0
            if not activity in self.awaited_activities[leading_type]:
                self.awaited_activities[leading_type].add(activity)
                self.awaited_objects[leading_type] = self.awaited_objects[leading_type] + 1


class CPN_Transition(SemanticNetNode):
    __explicit_default = "false"
    name: str
    transition_type: TransitionType
    __leading_object_type: str
    x: str
    y: str
    guard: str
    delay: str
    code: str
    priority: str
    routing_guard: RoutingGuard
    is_subpage_transition: bool
    ports: []

    def __init__(self, transition_type: TransitionType, name, x, y, cpn_id_manager: CPN_ID_Manager,
                 guard: str = None, delay: str = None, code: str = None, priority: str = None,
                 portsock_info: str = None, subpage=None, coordinate_scaling_factor=1.0):
        tag = "trans"
        self.cpn_id_manager = cpn_id_manager
        self.name = name
        self.transition_type = transition_type
        self.x = str(coordinate_scaling_factor * float(x))
        self.y = str(coordinate_scaling_factor * float(y))
        self.guard = guard
        self.delay = delay
        self.code = code
        self.priority = priority
        self.routing_guard = None
        self.subpage = subpage
        self.portsock_info = portsock_info
        self.ports = []
        fill_colour = "Gray" if transition_type is TransitionType.SILENT else "White"
        line_colour = "Gray" if transition_type is TransitionType.SILENT else "Black"
        text_colour = "White" if transition_type is TransitionType.SILENT else "Black"
        attributes = dict()
        attributes["explicit"] = self.__explicit_default
        child_elements = []
        child_elements.append(Posattr(x, y))
        child_elements.append(Fillattr("", colour=fill_colour))
        child_elements.append(Lineattr("1", colour=line_colour))
        child_elements.append(Textattr(colour=text_colour))
        child_elements.append(Text(name))
        child_elements.append(Box(name))
        child_elements.append(Binding())
        child_elements.append(Guard(x, y, cpn_id_manager, guard))
        child_elements.append(Time(x, y, cpn_id_manager, delay))
        child_elements.append(Code(x, y, cpn_id_manager, code))
        child_elements.append(Priority(x, y, cpn_id_manager, priority))
        if portsock_info is not None:
            child_elements.append(Substitution(x, y, cpn_id_manager, subpage.description, subpage.get_id, portsock_info))
        SemanticNetNode.__init__(self, tag, cpn_id_manager, attributes, child_elements)
        self.is_subpage_transition = False

    @classmethod
    def fromTransition(cls, transition):
        transition_type = transition.transition_type
        name = transition.name
        x = transition.x
        y = transition.y
        cpn = transition.cpn
        guard = transition.guard
        delay = transition.delay
        code = transition.code
        priority = transition.priority
        leading_object_type = transition.leading_object_type
        new_transition = cls(transition_type, name, x, y, cpn, guard, delay, code, priority, leading_object_type)
        return new_transition

    def add_substitution_info(self, subpage, portsock_map=None):
        if portsock_map is None:
            portsock_map = dict()
        old_portsock_info = self.portsock_info
        portsock_info = ""
        for new_place, old_place in portsock_map.items():
            portsock_info = portsock_info + "(" + new_place.get_id() + "," + old_place.get_id() + ")"
            self.ports.append(new_place)
        new_portsock_info = old_portsock_info + portsock_info \
            if not old_portsock_info is None else portsock_info
        substitution = Substitution(self.x, self.y, self.cpn_id_manager, subpage.name, subpage.get_id(), new_portsock_info)
        self.portsock_info = new_portsock_info
        self.child_elements = [child for child in self.child_elements if not isinstance(child, Substitution)]
        self.add_child(substitution)

    def has_port(self, port_id):
        return len(list(filter(lambda port: port.get_id() == port_id, self.ports))) > 0

    def set_guard(self, guard_text: str):
        guard_element: Guard = list(filter(lambda c: isinstance(c, Guard), self.child_elements))[0]
        self.guard = guard_text
        guard_element.set_text_content(guard_text)

    def set_name(self, name: str):
        text_element: Text = list(filter(lambda c: isinstance(c, Text), self.child_elements))[0]
        self.name = name
        text_element.set_text(name)

    def set_code(self, code_text: str):
        code_element: Code = list(filter(lambda c: isinstance(c, Code), self.child_elements))[0]
        text_element = code_element.text_element
        text_element.set_text(code_text)

    def set_delay(self, delay_text: str):
        delay_element: Time = list(filter(lambda c: isinstance(c, Time), self.child_elements))[0]
        text_element = delay_element.text_element
        text_element.set_text(delay_text)

    def set_standard_code_and_guard(self):
        name = self.name
        is_pack_transition = name[:3] == "pck"
        is_dly_transition = name[:3] == "dly"
        is_rel_transition = name[:3] == "RLS"
        # Cast to set! Mind that multiplicities might be helpful too at synchronization points
        input_vars = set(map(lambda arc: arc.annotation.text_element.get_text(), self.incoming_arcs))
        input_single_vars = [var for var in input_vars if "_s" not in var]
        input_many_vars = [var for var in input_vars if "_s" in var]
        joined_single_vars = ",".join(input_single_vars)
        joined_many_vars = "^^".join(input_many_vars)
        joined_vars = ",".join(input_vars)
        input = "input(" + joined_vars + ")"
        action = 'action(execute("' + name + '",'
        if len(joined_single_vars) > 0:
            action += '[' + joined_single_vars + "]"
        if len(joined_single_vars) > 0 and len(joined_many_vars) > 0 and not is_pack_transition:
            action += "^^"
        if len(joined_many_vars) > 0 and not is_pack_transition:
            action += joined_many_vars
        action += "))"
        code = input + ";" + action + ";"
        self.set_code(code)
        if not is_dly_transition and not \
                (is_rel_transition and self.subpage is not None and self.subpage.subpage_transition.name[
                                                                    :4] == "END_"):  # and not is_rel_transition:# self.guard is None:
            guard = "[binding_legal"
            if self.transition_type == TransitionType.ACTIVITY:
                guard += "_act"
            guard += "(" + '"' + self.name + '"' + ","
            if len(joined_single_vars) > 0:
                guard += "[" + joined_single_vars + "]"
            if len(joined_single_vars) > 0 and len(joined_many_vars) > 0 and not is_pack_transition:
                guard += "^^"
            if len(joined_many_vars) > 0 and not is_pack_transition:
                guard += joined_many_vars
            guard += ")]"
            self.set_guard(guard)

    def add_routing_guard(self):
        self.routing_guard = RoutingGuard(self.name + "_routing_guard", self.x, str(float(self.y) + 50.0))

    def has_routing_guard(self):
        return self.routing_guard is not None

    def clean_annotations_because_of_subpage_transformation(self):
        self.set_guard("")
        self.set_code("")
        self.set_delay("")

    def is_subpage_transition(self):
        return self.is_subpage_transition
