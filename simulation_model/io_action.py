from causal_model.causal_process_structure import CPM_Attribute, CPM_Categorical_Attribute
from simulation_model.timing import TimeInterval

VALSEP_CONSTANT = "SEP"
LIST2STRING_CONVERTER_NAME = "list2string"
MODEL_TIME_GETTER_NAME = "Mtime"
START_TIME_GETTER_NAME = "start_time"
NOW_TIME_GETTER_NAME = "now"
TIME2STRING_CONVERTER_NAME = "t2s"
EAVAL2LIST_CONVERTER_NAME = "eaval2list"
RECORD_WRITER_NAME = "write_record"
EVENT_WRITER_NAME = "write_event"
# TODO: Make start time parametrizable
PROCESS_START_TIMESTAMP = str(TimeInterval(days=20055, hours=8).get_seconds()) + ".0"


class ActivityIOAction:

    def __init__(self, activity_id, event_attributes: list[CPM_Attribute]):
        self.activity_id = activity_id
        self.event_attributes = event_attributes

    def to_SML(self):
        pass

class IOActionManager:

    def __init__(self):
        self.activity_actions = {}

    def make_activity_action(self,
                             activity_id,
                             ea
                             ):
        pass


def get_valsep_constant_sml():
    return '''
    val {0} = ";";
    '''.format(VALSEP_CONSTANT)


def get_list2string_converter_sml():
    return '''
    fun {0}([]) = ""|
    list2string(x::l) = x ^ (if l=[] then "" else {1}) ^ list2string(l);    
    '''.format(LIST2STRING_CONVERTER_NAME, VALSEP_CONSTANT)


def get_start_time_getter_sml():
    return '''
    fun {0}() = {1};
    '''.format(START_TIME_GETTER_NAME, PROCESS_START_TIMESTAMP)


def get_model_time_getter_sml():
    return '''
    fun {0}() = ModelTime.time():time;     
    '''.format(MODEL_TIME_GETTER_NAME)


def get_time2string_converter_sml():
    return '''
    fun {0}(t) = Date.fmt "%Y-%m-%d %H:%M:%S" (Date.fromTimeLocal(Time.fromReal(t+{1}())));    
    '''.format(
        TIME2STRING_CONVERTER_NAME,
        START_TIME_GETTER_NAME
    )


def get_now_time_getter_sml():
    return '''
    fun {0}() = toReal(Mtime());    
    '''.format(NOW_TIME_GETTER_NAME)


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
    '''.format(RECORD_WRITER_NAME)


def get_activity_event_table_initializer_name(activity_id: str):
    return "create_event_table_{0}".format(activity_id)


def get_activity_event_table_initializer_sml(activity_id: str, attribute_names: list[str]):
    return '''
    fun {0}() = 
    let
       val file_id = TextIO.openOut("./event_{1}.csv")
       val _ = TextIO.output(file_id, {2}(["event_id", "case_id", "activity", "timestamp"]^^{3})) 
       val _ = TextIO.output(file_id, "\\n")
    in
       TextIO.closeOut(file_id)
    end;
    '''.format(get_activity_event_table_initializer_name(activity_id),
               activity_id, LIST2STRING_CONVERTER_NAME,
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


def get_eaval2list_converter_name(act_id: str):
    return "{0}_{1}".format(EAVAL2LIST_CONVERTER_NAME, act_id)


def get_eaval2list_converter_sml(act_id: str, eaval_colset_name: str,
                                 event_attributes: list[CPM_Categorical_Attribute]):
    """
    A function to help converting an instance of the eaval-colset into a list of strings

    :param act_id: The activity for which the event attributes are to be converted
    :param eaval_colset_name: The colset name of the event attributes of that activity
    :param event_attributes: The categorical attributes that form the event attributes
    :return: The list of strings
    """
    number_of_attributes = len(event_attributes)
    sml = '''
    fun {0}(v_eaval: {1}) =
    let 
    '''.format(
        get_eaval2list_converter_name(act_id),
        eaval_colset_name
    )
    sml += "\n".join([
        "val x{0} = #{0} v_eaval".format(
            i + 2
        ) for i in range(number_of_attributes)
    ])
    sml += '''
    in
        [{0}]
    end;
    '''.format(
        ",".join([
            "{0}({1})".format(
                get_label_to_string_converter_name(event_attributes[i]),
                "x{0}".format(str(i+2))
            ) for i in range(number_of_attributes)
        ])
    )
    return sml


def get_event_writer_sml(activity_id: str, activity_name: str, eaval_colset_name: str):
    """
    A function for writing an event, taking an event id, the activity name, and ordered event attribute values.

    :return: The SML code
    """
    return '''
    fun {0}(event_counter: INT, activity_name: string, eaval: {2}) = 
    let
        val event_id = "EVENT" ^ Int.toString event_counter
        val event_file_id = "./event_{3}.csv"
        val case_id = #1 eaval
        val date = t2s(now())
        val _ = write_record(event_file_id, [event_id, case_id, "{1}", date]^^{4}(eaval))
    in
       ()
    end;        
    '''.format(get_activity_event_writer_name(activity_id), activity_name, eaval_colset_name,
               activity_id, get_eaval2list_converter_name(activity_id))


def get_all_standard_functions_ordered_sml():
    all_standard_functions_ordered = [
        (VALSEP_CONSTANT, get_valsep_constant_sml()),
        (LIST2STRING_CONVERTER_NAME, get_list2string_converter_sml()),
        (MODEL_TIME_GETTER_NAME, get_model_time_getter_sml()),
        (START_TIME_GETTER_NAME, get_start_time_getter_sml()),
        (TIME2STRING_CONVERTER_NAME, get_time2string_converter_sml()),
        (NOW_TIME_GETTER_NAME, get_now_time_getter_sml()),
        (RECORD_WRITER_NAME, get_record_writer_sml())
    ]
    return all_standard_functions_ordered
