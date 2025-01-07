from object_centric.object_type_structure import ObjectType
from simulation_model.colset import ColsetManager

PROJECT_OBJECT_TYPE_TO_IDS_FUNCTION_NAME = "project_to_ids"
EXTRACT_OBJECT_TYPE_BY_IDS_FUNCTION_NAME = "extract_by_ids"
SORTED_OBJECT_INSERT_FUNCTION_NAME = "sorted_insert"
MATCH_ONE_RELATION_FUNCTION_NAME = "match"
COMPLETENESS_BY_RELATIONS_FUNCTION_NAME = "complete"
CODE_FOR_TRANSITION_FUNCTION_NAME = "code"


def get_project_object_type_to_ids_function_name(ot: ObjectType):
    return "{0}_{1}".format(PROJECT_OBJECT_TYPE_TO_IDS_FUNCTION_NAME, ot.get_id())


def get_extract_object_type_by_ids_function_name(ot: ObjectType):
    return "{0}_{1}".format(EXTRACT_OBJECT_TYPE_BY_IDS_FUNCTION_NAME, ot.get_id())


def get_sorted_object_insert_function_name(ot: ObjectType):
    return "{0}_{1}".format(SORTED_OBJECT_INSERT_FUNCTION_NAME, ot.get_id())


def get_match_one_relation_function_name(ot1: ObjectType, ot2: ObjectType):
    """
    :param ot1: The object type that has a to-one relation to the other type.
    :param ot2: The object type of which exactly one object relates to an object of the other type
    :return: The name of the match_one_relation function
    """
    return "{0}_{1}_{2}".format(MATCH_ONE_RELATION_FUNCTION_NAME, ot1.get_id(), ot2.get_id())


def get_completeness_by_relations_function_name(ot1: ObjectType, ot2: ObjectType):
    """
    :param ot1: The object type that has a to-many relation to the other type.
    :param ot2: The object type of which many objects relate to an object of the other type
    :return: The name of the completeness_by_relations function
    """
    return "{0}_{1}_{2}".format(COMPLETENESS_BY_RELATIONS_FUNCTION_NAME, ot1.get_id(), ot2.get_id())


def get_code_for_transition_name(transition_id: str):
    return "{0}_{1}".format(CODE_FOR_TRANSITION_FUNCTION_NAME, transition_id)


def get_project_object_type_to_ids_function_sml(ot: ObjectType, colset_manager: ColsetManager):
    ot_list_colset_name: str = colset_manager.get_object_type_list_colset_name(ot)
    return "fun {0}([]) = [] | {0}(x::xs: {1}) = (#1 x)::{0}(xs)".format(
        get_project_object_type_to_ids_function_name(ot),
        ot_list_colset_name
    )


def get_extract_object_type_by_ids_function_sml(ot: ObjectType, colset_manager: ColsetManager):
    ot_list_colset_name = colset_manager.get_object_type_list_colset_name(ot)
    return '''fun {0}(is: {1}, []) = []  
           | {0}([], x::xs) = []   
           | {0}(i::is, x::xs) = 
           if (#1 i = x) then i::{0}(is, xs) 
           else if (#1 i < x) then  {0}(is, x::xs) 
           else {0}(i::is, xs)
           '''.format(
        get_extract_object_type_by_ids_function_name(ot),
        ot_list_colset_name
    )


def get_sorted_object_insert_function_sml(ot: ObjectType, colset_manager: ColsetManager):
    ot_colset_name = colset_manager.get_object_type_colset_name(ot)
    ot_list_colset_name = colset_manager.get_object_type_list_colset_name(ot)
    return "fun {0}(x, []) = [x] | {0}(x: {1}, y::ys: {2}) = if (#1 x) < (#1 y) then x::(y::ys) else y::{0}(x, ys);".format(
        get_sorted_object_insert_function_name(ot),
        ot_colset_name,
        ot_list_colset_name,
    )


def get_match_one_relation_function_sml(ot1: ObjectType, ot2: ObjectType, colset_manager: ColsetManager):
    """
    This function checks for two objects o1, o2 of types ot1, ot2 whether o2 is the unique object
    of type ot2 to which o1 relates to.

    :param ot1: The object type that has a to-one relation to the other type.
    :param ot2: The object type of which exactly one object relates to an object of the other type
    :param colset_manager: A ColsetManager that knows how relevant colsets are addressed.
    :return: The code of the match_one_relation_function
    """
    ot1_colset_name = colset_manager.get_object_type_colset_name(ot1)
    ot2_colset_name = colset_manager.get_object_type_colset_name(ot2)
    ot2_id_colset_name = colset_manager.get_object_type_ID_colset_name(ot2)
    ot2_at_ot1_index = colset_manager.get_subcol_index_by_names(ot1_colset_name, ot2_id_colset_name)
    return "fun {0}(o1: {1}, o2: {2}) = ((#{3} o1)=(#1 o2))".format(
        get_match_one_relation_function_name(ot1, ot2),
        ot1_colset_name,
        ot2_colset_name,
        ot2_at_ot1_index
    )


def get_completeness_by_relations_function_sml(ot1: ObjectType, ot2: ObjectType, colset_manager: ColsetManager):
    ot1_colset_name = colset_manager.get_object_type_colset_name(ot1)
    ot2_id_list_colset_name = colset_manager.get_object_type_ID_list_colset_name(ot2)
    ot2_list_colset_name = colset_manager.get_object_type_list_colset_name(ot2)
    ot2_at_ot1_index = colset_manager.get_subcol_index_by_names(ot1_colset_name, ot2_id_list_colset_name)
    return '''fun {0}(x: {1}, ys: {2}) = (#{3} x) = {4}({5}(ys, (#{3} x)))'''.format(
        get_completeness_by_relations_function_name(ot1, ot2),
        ot1_colset_name,
        ot2_list_colset_name,
        ot2_at_ot1_index + 1,  # CPNs count from 1, Python counts from 0.
        get_project_object_type_to_ids_function_name(ot2),
        get_extract_object_type_by_ids_function_name(ot2)
    )


def get_code_input_parameter_string(inputs, input_colset_names=None):
    if input_colset_names is None:
        return ",".join(inputs)
    return ",".join(["{0}: {1}".format(inputs[i], input_colset_names[i]) for i in range(len(inputs))])


def get_code_output_parameter_string(outputs):
    output_vars = list(filter(lambda o: o is not None, outputs))
    output_string = "({0})".format(",".join(output_vars))
    return output_string


def get_code_for_transition_sml(transition_id: str, inputs, input_colset_names, outputs, actions):
    parameter_string = get_code_input_parameter_string(inputs, input_colset_names)
    instructions = []
    for i in range(len(outputs)):
        output = outputs[i]
        action = actions[i]
        if output is None:
            instruction = "val _ = {0}".format(actions)
        else:
            instruction = "val {0} = {1}".format(output, action)
        instructions.append(instruction)
    code_string = "\n".join(instructions)
    output_string = get_code_output_parameter_string(outputs)
    return '''
    fun {0}({1}) = 
    let
    {2}
    in 
    {3}
    end;
    '''.format(
        get_code_for_transition_name(transition_id),
        parameter_string,
        code_string,
        output_string
    )
