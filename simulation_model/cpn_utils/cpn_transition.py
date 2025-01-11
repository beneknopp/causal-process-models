import warnings
from enum import Enum

from causal_model.causal_process_structure import CPM_Activity
from simulation_model.functions import get_code_for_transition_name as get_code_for_transition_name_global
from object_centric.object_type_structure import ObjectType
from simulation_model.cpn_utils.semantic_net_node import SemanticNetNode
from simulation_model.cpn_utils.xml_utils.attributes import Posattr, Lineattr, Textattr, Fillattr
from simulation_model.cpn_utils.xml_utils.cpn_id_managment import CPN_ID_Manager
from simulation_model.cpn_utils.xml_utils.cpn_node import CPN_Node
from simulation_model.cpn_utils.xml_utils.dom_element import DOM_Element
from simulation_model.cpn_utils.xml_utils.layout import Text, Box
from object_centric.object_centric_petri_net import ObjectCentricPetriNetTransition as OCPN_Transition
from simulation_model.functions import get_code_for_transition_sml, get_code_output_parameter_string


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
    conjuncts = []

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

    def add_conjunct(self, conjunct: str):
        """
        Add to the conjuncts, the condition to be connected with AND to form the guard
        :param conjunct: a string representation of the conjunct
        """
        self.conjuncts = self.conjuncts + [conjunct]
        self.convert_conjuncts_to_guard()

    def convert_conjuncts_to_guard(self):
        """
        Make a conjunction over all conjuncts and override the guard condition with it.
        """
        guard_text = "andalso".join(["({0})".format(c) for c in self.conjuncts])
        guard_text = "[" + guard_text + "]"
        self.set_text_content(guard_text)


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


class CodeManager:
    '''
    fun guard_place_order(x: C_orders, ys: C_items_LIST)=
    let
    val items_complete = extract_items_by_ids(ys, (#2 x))
    val products_complete = extract_products_by_ids(ys, (#2 x))
    in
    items_complete, products_complete
    end;
    '''

    def __init__(self, transition_id: str, activity: CPM_Activity):
        """
        This class makes it possible to dynamically add code to transitions during constructing the CPN.
        In our case, for example, we want to synchronize object flows by means of object relations and for this,
        delegate some logic into the code region.
        """
        self.transition_id = transition_id
        self.activity = activity
        self.input_variables = []
        self.non_event_writing_actions = []
        self.non_event_writing_output_variables = []
        self.event_writing_action: tuple[str, CPM_Activity, list[str], list[str]] | None = None
        self.__has_code = False
        self.__delay_output = None
        self.__start_time_output = None
        self.__complete_time_output = None
        self.delay_variables_by_object_type: dict[ObjectType, str] = dict()

    def add_input_variables(self, input_variables: list[str]):
        for i in range(len(input_variables)):
            input_var = input_variables[i]
            if input_var in self.input_variables:
                warnings.warn(
                    "Trying to add existing input variable '{0}' to code region, I'm ignoring this.".format(input_var))
            self.input_variables.append(input_var)

    def add_output(self, output: str, output_time_object_types: list[ObjectType], is_event_writing: bool = False):
        if len(output_time_object_types):
            for ot in output_time_object_types:
                self.delay_variables_by_object_type[ot] = output
            return
        self.non_event_writing_output_variables.append(output)

    def add_action(self, action: str, input_parameters: list[str], input_variables_colset_names: list[str],
                   is_event_writing=False):
        if not is_event_writing:
            self.non_event_writing_actions.append((action, input_parameters, input_variables_colset_names))
        else:
            self.event_writing_action = (action, self.activity, input_parameters, input_variables_colset_names)
        self.__has_code = True

    def get_code_name(self):
        return get_code_for_transition_name_global(self.transition_id)

    def get_code_sml(self):
        return get_code_for_transition_sml(self.transition_id,
                                           self.non_event_writing_actions,
                                           self.non_event_writing_output_variables,
                                           self.event_writing_action,
                                           self.__start_time_output is not None,
                                           self.__complete_time_output is not None
                                           )

    def get_non_event_writing_actions(self):
        return

    def get_output_variables(self):
        output_variables = []
        time_variables = []
        for ot, delay_variable in self.delay_variables_by_object_type.items():
            if delay_variable not in time_variables:
                time_variables.append(delay_variable)
        time_variables += [self.__start_time_output] if self.__start_time_output is not None else []
        time_variables += [self.__complete_time_output] if self.__complete_time_output is not None else []
        output_variables = time_variables + self.non_event_writing_output_variables
        return output_variables

    def get_code_annotation(self):
        input_variables_string = ",".join(self.input_variables)
        output_variables = self.get_output_variables()
        output_variables_string = get_code_output_parameter_string(
            output_variables
        )
        all_input_parameters = []
        if self.event_writing_action is not None:
            _, _, event_writing_input_parameters, input_variables_colset_names = self.event_writing_action
            all_input_parameters += event_writing_input_parameters
        for _, params, _ in self.non_event_writing_actions:
            all_input_parameters += params
        input_parameter_string = ",".join(all_input_parameters)
        action_call = "{0}({1})".format(
            get_code_for_transition_name_global(self.transition_id),
            input_parameter_string
        )
        return "input({0});\noutput({1});\naction({2});".format(
            input_variables_string,
            output_variables_string,
            action_call)

    def has_code(self):
        return self.__has_code

    def add_start_time_output(self, start_time_output):
        """
        This function is specifically for adding a variable to the output of the transition
        that carries the start timestamp.
        These designated functions assure a variable sorting that is compliant with the way
        the variables are sorted in other code generation in this project.

        :start_time_output: The variable to which the start timestamp is to be bound
        """
        if self.__start_time_output is not None:
            return
        self.__start_time_output = start_time_output

    def add_complete_time_output(self, complete_time_output):
        """
        This function is specifically for adding a variable to the output of the transition
        that carries the completion timestamp.
        These designated functions assure a variable sorting that is compliant with the way
        the variables are sorted in other code generation in this project.

        :start_time_output: The variable to which the start timestamp is to be bound
        """
        if self.__complete_time_output is not None:
            return
        self.__complete_time_output = complete_time_output


class CPN_Transition(SemanticNetNode):
    __explicit_default = "false"
    name: str
    transition_type: TransitionType
    __leading_object_type: str
    x: str
    y: str
    guard_str: str
    guard: Guard
    delay: str
    code: str
    priority: str
    is_subpage_transition: bool
    ports: []

    def __init__(self, transition_type: TransitionType, name, x, y, cpn_id_manager: CPN_ID_Manager,
                 guard_str: str = None, delay: str = None, code: str = None, priority: str = None,
                 portsock_info: str = None, subpage=None, coordinate_scaling_factor=1.0,
                 activity: CPM_Activity = None,
                 ocpn_transition: OCPN_Transition = None):
        tag = "trans"
        self.cpn_id_manager = cpn_id_manager
        self.name = name
        self.transition_type = transition_type
        self.x = str(coordinate_scaling_factor * float(x))
        self.y = str(coordinate_scaling_factor * float(y))
        self.guard_str = guard_str
        self.delay = delay
        self.code = code
        self.priority = priority
        self.subpage = subpage
        self.portsock_info = portsock_info
        self.ports = []
        self.activity = activity
        self.code_manager = CodeManager("_".join(name.split(" ")), activity)
        self.ocpn_transition = ocpn_transition
        fill_colour = "Gray" if transition_type is TransitionType.SILENT else "White"
        line_colour = "Gray" if transition_type is TransitionType.SILENT else "Black"
        text_colour = "White" if transition_type is TransitionType.SILENT else "Black"
        attributes = dict()
        attributes["explicit"] = self.__explicit_default
        guard = Guard(x, y, cpn_id_manager, guard_str)
        self.guard = guard
        child_elements = []
        child_elements.append(Posattr(x, y))
        child_elements.append(Fillattr("", colour=fill_colour))
        child_elements.append(Lineattr("1", colour=line_colour))
        child_elements.append(Textattr(colour=text_colour))
        child_elements.append(Text(name))
        child_elements.append(Box(name))
        child_elements.append(Binding())
        child_elements.append(guard)
        child_elements.append(Time(x, y, cpn_id_manager, delay))
        child_elements.append(Code(x, y, cpn_id_manager, code))
        child_elements.append(Priority(x, y, cpn_id_manager, priority))
        if portsock_info is not None:
            child_elements.append(
                Substitution(x, y, cpn_id_manager, subpage.description, subpage.get_id, portsock_info))
        SemanticNetNode.__init__(self, tag, cpn_id_manager, attributes, child_elements)
        self.is_subpage_transition = False

    def add_guard_conjunct(self, conjunct: str):
        """
        Add to the conjuncts, the condition to be connected with AND to form the guard
        :param conjunct: a string representation of the conjunct
        """
        self.guard.add_conjunct(conjunct)

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

    def is_subpage_transition(self):
        return self.is_subpage_transition

    def add_code(self,
                 action_name: str,
                 input_variables: list[str],  # length k
                 input_parameters: list[str],  # length n >= k
                 input_parameters_colset_names: list[str],  # length n
                 output: str = None,
                 output_time_object_types=None,
                 is_event_writing: bool = False
                 ):
        """
        Add a function call to be added to the transition code segment.

        :param action_name: The name of the function to be called
        :param input_variables: All variables to which any input arguments is bound
        :param input_parameters: All input arguments
        :param input_parameters_colset_names: The colset names corresponding to the input arguments, sorted
        :param output: The variable to which the return of the function call is to be bound.
        :param output_time_object_type: If the output is variable carrying a timestamp (delay), the object type to
        which this timestamp is to be added after executing the transition.
        """
        if output_time_object_types is None:
            output_time_object_types = []
        self.code_manager.add_input_variables(input_variables)
        self.code_manager.add_output(output, output_time_object_types, is_event_writing)
        self.code_manager.add_action(action_name, input_parameters, input_parameters_colset_names, is_event_writing)
        code_annotation = self.code_manager.get_code_annotation()
        self.set_code(code_annotation)

    def has_code(self):
        return self.code_manager.has_code()

    def get_code_name(self):
        return self.code_manager.get_code_name()

    def get_code_sml(self):
        return self.code_manager.get_code_sml()

    def get_object_type_delay_variable(self, ot: ObjectType):
        if ot in self.code_manager.delay_variables_by_object_type:
            return self.code_manager.delay_variables_by_object_type[ot]

    def add_start_time_output(self, output):
        self.code_manager.add_start_time_output(output)

    def add_complete_time_output(self, output):
        self.code_manager.add_complete_time_output(output)

    def set_activity(self, activity):
        self.activity = activity
        self.code_manager.activity = activity
