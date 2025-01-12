from causal_model.causal_process_structure import CPM_Categorical_Attribute, CPM_Attribute, CPM_Domain_Type, \
    CPM_Activity
from simulation_model.colset import ColsetManager
from simulation_model.timing import TimeInterval, HourDensity, WeekdayDensity, TimeDensity, ProcessTimeCategory, \
    TimeUnit, TimeDensityCalendar

MINUTE_CONSTANT_NAME = "minute"
HOUR_CONSTANT_NAME = "hour"
DAY_CONSTANT_NAME = "day"
WEEK_CONSTANT_NAME = "week"
VALSEP_CONSTANT = "SEP"
LIST_DIFF_ELEMENT_FUNCTION_NAME = "list_diff_element"
LIST_DIFF_FUNCTION_NAME = "list_diff"
LIST2STRING_CONVERTER_NAME = "list2string"
MODEL_TIME_GETTER_NAME = "Mtime"
START_TIME_GETTER_NAME = "start_time"
NOW_TIME_GETTER_NAME = "now"
TIME2DATE_CONVERTER_NAME = "t2date"
TIMEUNIT_PROJECTOR_NAME = "t2projected_timeunit"
TIME2PROJECTED_TIMEUNIT_STRING_CONVERTER_NAME = TIMEUNIT_PROJECTOR_NAME + "_str"
TIME2STRING_CONVERTER_NAME = "t2s"
REMAINING_HOUR_GETTER_NAME = "remaining_time_hour"
TIME_DENSITY_GETTER_NAME = "time_density"
RELATIVE_DELAY_FUNCTION_NAME = "rel_delay"
RELATIVE_DELAY_FROM_NOW_FUNCTION_NAME = "rel_delay_from_now"
EFFICIENT_DELAY_FACTOR_NAME = "eff_del_factor"
NORMALIZED_DELAY_FUNCTION_NAME = "normalized_delay"
EAVAL2LIST_CONVERTER_NAME = "eaval2list"
RECORD_WRITER_NAME = "write_record"
EVENT_WRITER_NAME = "write_event"
CODE_FOR_TRANSITION_FUNCTION_NAME = "code"
# TODO: Make start time parametrizable
PROCESS_START_TIMESTAMP = str(TimeInterval(days=20055, hours=8).get_seconds()) + ".0"



def get_timeunit_constant_name(timeunit: TimeUnit):
    if timeunit == TimeUnit.MINUTE:
        return MINUTE_CONSTANT_NAME
    if timeunit == TimeUnit.HOUR:
        return HOUR_CONSTANT_NAME
    if timeunit == TimeUnit.DAY:
        return DAY_CONSTANT_NAME
    if timeunit == TimeUnit.WEEK:
        return WEEK_CONSTANT_NAME
    raise AttributeError("No timeunit constant defined for {0}".format(timeunit.value))


def get_valsep_constant():
    return VALSEP_CONSTANT


def get_list_diff_element_function_name():
    return LIST_DIFF_ELEMENT_FUNCTION_NAME


def get_list_diff_function_name():
    return LIST_DIFF_FUNCTION_NAME


def get_list2string_converter_name():
    return LIST2STRING_CONVERTER_NAME


def get_model_time_getter_name():
    return MODEL_TIME_GETTER_NAME


def get_start_time_getter_name():
    return START_TIME_GETTER_NAME


def get_now_time_getter_name():
    return NOW_TIME_GETTER_NAME


def get_time2date_converter_name():
    return TIME2DATE_CONVERTER_NAME


def get_timeunit_projector_name(timeunit: TimeUnit):
    return "{0}_{1}".format(TIMEUNIT_PROJECTOR_NAME, timeunit.value)


def get_time2projected_timeunit_string_converter_name(timeunit: TimeUnit):
    return "{0}_{1}".format(TIME2PROJECTED_TIMEUNIT_STRING_CONVERTER_NAME, timeunit.value)


def get_remaining_hour_getter_name():
    return REMAINING_HOUR_GETTER_NAME


def get_time2string_converter_name():
    return TIME2STRING_CONVERTER_NAME


def get_time_sub_density_getter_name(pt_cat: ProcessTimeCategory, timeunit: TimeUnit):
    return "{0}_{1}_{2}".format(TIME_DENSITY_GETTER_NAME, pt_cat.value.lower(), timeunit.value.lower())


def get_time_density_getter_name(pt_cat: ProcessTimeCategory):
    return "{0}_{1}".format(TIME_DENSITY_GETTER_NAME, pt_cat.value.lower())


def get_relative_delay_function_name(pt_cat: ProcessTimeCategory):
    return "{0}_{1}".format(RELATIVE_DELAY_FUNCTION_NAME, pt_cat.value.lower())


def get_relative_delay_from_now_function_name(pt_cat: ProcessTimeCategory):
    return "{0}_{1}".format(RELATIVE_DELAY_FROM_NOW_FUNCTION_NAME, pt_cat.value.lower())


def get_effective_delay_factor_name(pt_cat: ProcessTimeCategory):
    return EFFICIENT_DELAY_FACTOR_NAME + "_" + pt_cat.value.lower()


def get_normalized_delay_from_now_function_name(pt_cat: ProcessTimeCategory):
    return NORMALIZED_DELAY_FUNCTION_NAME + "_" + pt_cat.value.lower()


def get_eaval2list_converter_name(act_id: str):
    return "{0}_{1}".format(EAVAL2LIST_CONVERTER_NAME, act_id)


def get_record_writer_name():
    return RECORD_WRITER_NAME


def get_event_writer_name():
    return EVENT_WRITER_NAME


def get_process_start_timestamp():
    return PROCESS_START_TIMESTAMP

def get_code_for_transition_name(transition_id: str):
    return "{0}_{1}".format(CODE_FOR_TRANSITION_FUNCTION_NAME, transition_id)

def get_timeunit_constant_sml(timeunit: TimeUnit):
    if timeunit == TimeUnit.MINUTE:
        val_term = "60.0"
    elif timeunit == TimeUnit.HOUR:
        val_term = "60.0*{0}".format(get_timeunit_constant_name(TimeUnit.MINUTE))
    elif timeunit == TimeUnit.DAY:
        val_term = "24.0*{0}".format(get_timeunit_constant_name(TimeUnit.HOUR))
    elif timeunit == TimeUnit.WEEK:
        val_term = "7.0*{0}".format(get_timeunit_constant_name(TimeUnit.DAY))
    else:
        raise AttributeError("No timeunit constant defined for {0}".format(timeunit.value))
    return "val {0} = {1};".format(
        get_timeunit_constant_name(timeunit),
        val_term
    )


def get_valsep_constant_sml():
    return '''
    val {0} = ";";
    '''.format(get_valsep_constant())


def get_list2string_converter_sml():
    return '''
    fun {0}([]) = ""|
    list2string(x::l) = x ^ (if l=[] then "" else {1}) ^ list2string(l);    
    '''.format(get_list2string_converter_name(), get_valsep_constant())


def get_list_diff_element_function_sml():
    return "fun {0}([], _) = [] | {0}(y::xs, x) = ( if y=x then xs else y::{0}(xs, x))".format(
        get_list_diff_element_function_name()
    )


def get_list_diff_function_sml():
    return "fun {0}(l1, []) = l1 | list_diff(l1, h2::l2) = {0}({1}(l1, h2), l2)".format(
        get_list_diff_function_name(),
        get_list_diff_element_function_name()
    )


def get_time2date_converter_sml():
    return "fun {0}(t) = Date.fromTimeLocal(Time.fromReal(t+{1}()));".format(
        get_time2date_converter_name(),
        get_start_time_getter_name()
    )


def get_timeunit_projector_sml(timeunit: TimeUnit):
    if timeunit in [TimeUnit.SECOND, TimeUnit.MINUTE, TimeUnit.HOUR, TimeUnit.DAY, TimeUnit.MONTH, TimeUnit.YEAR]:
        sml_method_name = timeunit.value.lower()
    elif timeunit == TimeUnit.WEEKDAY:
        sml_method_name = "weekDay"
    else:
        raise AttributeError("Invalid Timeunit {0}".format(TimeUnit.value))
    if timeunit in [TimeUnit.MONTH, TimeUnit.WEEKDAY]:
        rettype = "Date.{0}".format(timeunit.value)
    elif timeunit in [TimeUnit.SECOND, TimeUnit.MINUTE, TimeUnit.HOUR, TimeUnit.DAY, TimeUnit.YEAR]:
        rettype = "int"
    else:
        raise AttributeError("Invalid Timeunit {0}".format(TimeUnit.value))
    return '''fun {0}(t) = Date.{1}({2}(t)):{3};'''.format(
        get_timeunit_projector_name(timeunit),
        sml_method_name,
        get_time2date_converter_name(),
        rettype
    )


def get_time2projected_timeunit_string_converter_sml(timeunit: TimeUnit):
    if timeunit == TimeUnit.WEEKDAY:
        iso_format_string = "a"
    elif timeunit == TimeUnit.MONTH:
        iso_format_string = "b"
    elif timeunit == TimeUnit.HOUR:
        iso_format_string = "H"
    else:
        raise AttributeError("Invalid Timeunit {0}".format(timeunit.value))
    return 'fun {0}(t) = Date.fmt "%{1}" (Date.fromTimeLocal(Time.fromReal(t+start_time())));'.format(
        get_time2projected_timeunit_string_converter_name(timeunit),
        iso_format_string
    )


def get_start_time_getter_sml():
    return '''
    fun {0}() = {1};
    '''.format(get_start_time_getter_name(), get_process_start_timestamp())


def get_model_time_getter_sml():
    return '''
    fun {0}() = ModelTime.time():time;     
    '''.format(MODEL_TIME_GETTER_NAME)


def get_now_time_getter_sml():
    return '''
    fun {0}() = toReal(Mtime());    
    '''.format(get_now_time_getter_name())


def get_timeunit2string_converter_name(timeunit: str):
    return "{0}_{1}".format(TIME2STRING_CONVERTER_NAME, timeunit)


def get_time2string_converter_sml():
    return '''
    fun {0}(t) = Date.fmt "%Y-%m-%d %H:%M:%S" (Date.fromTimeLocal(Time.fromReal(t+{1}())));    
    '''.format(
        get_time2string_converter_name(),
        get_start_time_getter_name()
    )


def get_remaining_hour_getter_sml():
    return "fun {0}(t) = {3} - ((Real.fromInt({1}(t))*{4}) + Real.fromInt({2}(t)));".format(
        get_remaining_hour_getter_name(),
        get_timeunit_projector_name(TimeUnit.MINUTE),
        get_timeunit_projector_name(TimeUnit.SECOND),
        get_timeunit_constant_name(TimeUnit.HOUR),
        get_timeunit_constant_name(TimeUnit.MINUTE)
    )


def get_time_sub_density_getter_sml(pt_cat: ProcessTimeCategory, timeunit: TimeUnit, density: TimeDensity):
    case_d = " | ".join([
        '"{0}" => {1}'.format(str(key), str(float(d)))
        for key, d in density.get_as_dict().items()
    ])
    case_d += " | _ => 1.0;"
    sml = '''
    fun {0}(d:string) =
    case d of {1}
    '''.format(
        get_time_sub_density_getter_name(pt_cat, timeunit),
        case_d
    )
    return sml


def get_time_density_getter_sml(pt_cat: ProcessTimeCategory):
    return '''
    fun {0}(t) = {1}({2}(t))*{3}({4}(t));
    '''.format(
        get_time_density_getter_name(pt_cat),
        get_time_sub_density_getter_name(pt_cat, TimeUnit.WEEKDAY),
        get_time2projected_timeunit_string_converter_name(TimeUnit.WEEKDAY),
        get_time_sub_density_getter_name(pt_cat, TimeUnit.HOUR),
        get_time2projected_timeunit_string_converter_name(TimeUnit.HOUR)
    )


def get_relative_delay_function_sml(pt_cat: ProcessTimeCategory):
    return '''
    fun {0}(t,d) =
        if d < 0.0001
        then 0.0
        else if d < {1}(t)*{2}(t)
            then d/{2}(t)
            else {0}(
                t + {1}(t),
                d - ({1}(t) * {2}(t))) + {3} ;
    '''.format(get_relative_delay_function_name(pt_cat),
               get_remaining_hour_getter_name(),
               get_time_density_getter_name(pt_cat),
               get_timeunit_constant_name(TimeUnit.HOUR)
               )


def get_relative_delay_from_now_function_sml(pt_cat: ProcessTimeCategory):
    return "fun {0}(d) = {1}({2}(),d);".format(
        get_relative_delay_from_now_function_name(pt_cat),
        get_relative_delay_function_name(pt_cat),
        get_now_time_getter_name()
    )


def get_effective_delay_factor_sml(pt_cat: ProcessTimeCategory):
    # return "val {0} = {1}(52.0*{2})/(52.0*{2});".format(
    # get_effective_delay_factor_name(pt_cat),
    # get_relative_delay_from_now_function_name(pt_cat),
    # get_timeunit_constant_name(TimeUnit.WEEK)
    # )
    return "val {0} = 1.0;".format(get_effective_delay_factor_name(pt_cat))


def get_normalized_delay_from_now_function_sml(pt_cat: ProcessTimeCategory):
    return "fun {0}(d) = {1}(d / {2});".format(
        get_normalized_delay_from_now_function_name(pt_cat),
        get_relative_delay_from_now_function_name(pt_cat),
        get_effective_delay_factor_name(pt_cat)
    )


def get_record_writer_sml():
    """
    A generic function for writing a list of strings to .csv.

    :return: The SML code
    """
    return '''
    fun {0}(file_id, l) = 
    let
       val file = TextIO.openAppend(file_id)
       val _ = TextIO.output(file, list2string(l))
       val _ = TextIO.output(file, "\\n")
    in
       TextIO.closeOut(file)
    end;    
    '''.format(get_record_writer_name())


def get_activity_event_table_initializer_name(activity_id: str):
    return "create_event_table_{0}".format(activity_id)


def get_event_table_file_path(activity_id: str, model_name: str):
    return "./{0}_event_{1}.csv".format(model_name, activity_id)


def get_activity_event_table_initializer_sml(activity_id: str, attribute_names: list[str], model_name: str):
    return '''
    fun {0}() = 
    let
       val file_id = TextIO.openOut("{1}")
       val _ = TextIO.output(file_id, {2}(["event_id", "case_id", "activity", "start_timestamp", "end_timestamp"]^^{3})) 
       val _ = TextIO.output(file_id, "\\n")
    in
       TextIO.closeOut(file_id)
    end;
    '''.format(get_activity_event_table_initializer_name(activity_id),
               get_event_table_file_path(activity_id, model_name),
               LIST2STRING_CONVERTER_NAME,
               "[" + ",".join(['"' + attr_name + '"' for attr_name in attribute_names]) + "]")


def get_activity_event_writer_name(activity_id: str):
    return "{0}_{1}".format(EVENT_WRITER_NAME, activity_id)


def get_label_to_string_converter_name(attribute: CPM_Categorical_Attribute):
    return "label_to_string_{0}".format(attribute.get_id())


def get_label_to_string_converter_sml(attribute: CPM_Categorical_Attribute, colset_name: str):
    """
    A function to convert the labels of a categorical attribute (WITH colset) into strings.

    :param attribute: The attribute with labels to be converted
    :param colset_name: The name of the attribute domain colset
    :return: The SML code
    """
    labels = attribute.get_labels()
    fun_body = "fun {0}(x: {1}) =".format(get_label_to_string_converter_name(attribute), colset_name)
    fun_body += "\ncase x of "
    fun_body += " | ".join(['{0} => "{0}"'.format(label) for label in labels]) + ";"
    return fun_body


def get_eaval2list_converter_sml(act_id: str,
                                 local_event_attributes: list[CPM_Attribute],
                                 local_event_attributes_colset_names: list[str]):
    """
    A function to help converting an instance of the eaval-colset into a list of strings

    :param act_id: The activity for which the event attributes are to be converted
    :param local_event_attributes: The attributes that form the event attributes
    :param local_event_attributes_colset_names: The colset name of the event attributes of that activity

    :return: the SML function code to convert the list of attribute values into a list of strings
    """
    categorical_attributes_indices = [i for i, attr in enumerate(local_event_attributes)
                                      if attr.get_domain_type() is CPM_Domain_Type.CATEGORICAL]
    sml = '''
    fun {0}({1}) = 
    '''.format(
        get_eaval2list_converter_name(act_id),
        ",".join(["x{0}: {1}".format(str(i), local_event_attributes_colset_names[i])
                  for i in range(len(local_event_attributes))])
    )
    eaval_categorical_as_string_expressions = [
        "{0}({1})".format(get_label_to_string_converter_name(local_event_attributes[i]), "x{0}".format(str(i))
                          ) for i in categorical_attributes_indices]
    all_eaval_as_string_expressions = \
        eaval_categorical_as_string_expressions
    sml += "[" + ",".join(all_eaval_as_string_expressions) + "]"
    return sml


def get_event_writer_sml(activity_id: str,
                         activity_name: str,
                         local_event_attributes_colset_names: list[str],
                         model_name: str):
    """
    A function for writing an event, taking an event id, the activity name, and ordered event attribute values.

    :return: The SML code
    """
    local_event_attributes_string = ",".join(
        ["x{0}: {1}".format(str(i), colset_name) for i, colset_name in enumerate(local_event_attributes_colset_names)])
    return '''
    fun {0}(event_counter: INT, case_id: STRING, delay: real{1}{2}) = 
    let
        val event_id = "EVENT" ^ Int.toString event_counter
        val event_file_id = "{3}"
        val start_time = {4}()
        val norm_delay = {5}(delay) 
        val end_time = start_time + delay
        val _ = {8}(event_file_id, [event_id, case_id, "{6}", {9}(start_time), {9}(end_time)]^^{7}({2}))
    in
       (ModelTime.fromInt(round(norm_delay)), start_time, end_time)
    end;        
    '''.format(
        get_activity_event_writer_name(activity_id),
        "," if len(local_event_attributes_string) else "",
        local_event_attributes_string,
        get_event_table_file_path(activity_id, model_name),
        get_now_time_getter_name(),
        get_normalized_delay_from_now_function_name(ProcessTimeCategory.SERVICE),
        activity_name,
        get_eaval2list_converter_name(activity_id),
        get_record_writer_name(),
        get_time2string_converter_name()
    )

def get_code_output_parameter_string(outputs):
    output_vars = list(filter(lambda o: o is not None, outputs))
    output_string = ",".join(output_vars)
    return output_string


def get_code_for_transition_sml(transition_id: str,
                                other_actions: list[tuple[str, list[str], list[str]]],
                                other_output_variables: list[str],
                                event_writing_action: tuple[str, CPM_Activity, list[str], list[str]] = None,
                                return_start_time: bool = None, return_complete_time: bool = None
                                ):
    instructions = []
    input_params = []
    event_time_outputs = []
    other_outputs = []
    j = 1
    if event_writing_action is not None:
        event_writing_output_variable = "x"
        action, activity, _, colsetnames = event_writing_action
        event_writer_name = get_activity_event_writer_name(activity.get_id())
        event_time_outputs.append("#1 {0}".format(event_writing_output_variable))
        if return_start_time:
            event_time_outputs.append("#2 {0}".format(event_writing_output_variable))
        if return_complete_time:
            event_time_outputs.append("#3 {0}".format(event_writing_output_variable))
        action_params = []
        for cn in colsetnames:
            action_params.append("x{0}".format(str(j), cn))
            input_params.append("x{0}: {1}".format(str(j), cn))
            j = j + 1
        action_parameter_string = ",".join(action_params)
        event_writing_instruction = "val {0} = {1}({2})".format(event_writing_output_variable, action, action_parameter_string)
        instructions.append(event_writing_instruction)
    for i in range(len(other_actions)):
        output = other_output_variables[i]
        other_outputs.append(output)
        action, _, colsetnames = other_actions[i]
        action_params = []
        for cn in colsetnames:
            action_params.append("x{0}".format(str(j), cn))
            input_params.append("x{0}: {1}".format(str(j), cn))
            j = j + 1
        action_parameter_string = ",".join(action_params)
        if output is None:
            instruction = "val _ = {0}({1})".format(action, action_parameter_string)
        else:
            instruction = "val {0} = {1}({2})".format(output, action, action_parameter_string)
        instructions.append(instruction)
    input_parameter_string = ",".join(input_params)
    code_string = "\n".join(instructions)
    output_string = get_code_output_parameter_string(event_time_outputs + other_outputs)
    sml = "fun {0}({1}) = let {2} in ({3}) end;".format(
        get_code_for_transition_name(transition_id),
        input_parameter_string,
        code_string,
        output_string
    )
    return sml


def get_all_standard_functions_ordered_sml():
    """
    This is the first batch of standard functions.
    The logic of arrival/service time densities depends on some of those.

    :return:
    """
    all_standard_functions_ordered = [
        (get_timeunit_constant_name(timeunit), get_timeunit_constant_sml(timeunit))
        for timeunit in [TimeUnit.MINUTE, TimeUnit.HOUR, TimeUnit.DAY, TimeUnit.WEEK]
    ]
    all_standard_functions_ordered += [
        (get_valsep_constant(), get_valsep_constant_sml()),
        (get_list2string_converter_name(), get_list2string_converter_sml()),
        (get_list_diff_element_function_name(), get_list_diff_element_function_sml()),
        (get_list_diff_function_name(), get_list_diff_function_sml()),
        (get_model_time_getter_name(), get_model_time_getter_sml()),
        (get_start_time_getter_name(), get_start_time_getter_sml()),
        (get_now_time_getter_name(), get_now_time_getter_sml()),
        # (get_time2string_converter_name(), get_time2string_converter_sml()),
        (get_time2date_converter_name(), get_time2date_converter_sml()),
    ]
    all_standard_functions_ordered += [
        (get_timeunit_projector_name(timeunit), get_timeunit_projector_sml(timeunit))
        for timeunit in TimeUnit if timeunit is not TimeUnit.WEEK
    ]
    all_standard_functions_ordered += [
        (get_time2projected_timeunit_string_converter_name(timeunit),
         get_time2projected_timeunit_string_converter_sml(timeunit))
        for timeunit in [TimeUnit.WEEKDAY, TimeUnit.HOUR]
    ]
    all_standard_functions_ordered += [
        (get_time2string_converter_name(), get_time2string_converter_sml()),
        (get_remaining_hour_getter_name(), get_remaining_hour_getter_sml())
    ]
    return all_standard_functions_ordered


def get_all_timing_functions_ordered_sml(pt_cat_density_map: dict[ProcessTimeCategory, TimeDensityCalendar]):
    function_smls: list[tuple[str, any]] = []
    h = TimeUnit.HOUR
    wd = TimeUnit.WEEKDAY
    for c, d in pt_cat_density_map.items():
        function_smls += [
            (get_time_sub_density_getter_name(c, h), get_time_sub_density_getter_sml(c, h, d.hour_density)),
            (get_time_sub_density_getter_name(c, wd), get_time_sub_density_getter_sml(c, wd, d.weekday_density)),
            (get_time_density_getter_name(c), get_time_density_getter_sml(c)),
            (get_relative_delay_function_name(c), get_relative_delay_function_sml(c)),
            (get_relative_delay_from_now_function_name(c), get_relative_delay_from_now_function_sml(c)),
            (get_effective_delay_factor_name(c), get_effective_delay_factor_sml(c)),
            (get_normalized_delay_from_now_function_name(c), get_normalized_delay_from_now_function_sml(c))
        ]
    return function_smls


def get_all_event_functions_ordered_sml():
    all_standard_functions_ordered = [
        (get_record_writer_name(), get_record_writer_sml())
    ]
    return all_standard_functions_ordered
