from causal_model.causal_process_model import CausalProcessModel, AggregationSelections, AggregationFunctions, \
    AttributeValuations
from causal_model.causal_process_structure import CausalProcessStructure, AttributeActivities, \
    CPM_Activity, \
    AttributeRelation, CPM_Categorical_Attribute
from causal_model.valuation import BayesianValuation, ValuationParameters, ValuationParameter
from object_model.object_type_structure import ObjectType, ObjectTypeStructure, ObjectTypeRelation, Multiplicity
from process_model.petri_net import SimplePetriNet, LabelingFunction, \
    SimplePetriNetPlace as Place, SimplePetriNetTransition as Transition, SimplePetriNetArc as Arc, \
    ObjectCentricPetriNet, ObjectCentricPetriNetArc as OCPN_Arc, ObjectCentricPetriNetPlace as OCPN_Place,\
    ObjectCentricPetriNetTransition as OCPN_Transition
from simulation_model.simulation_model import SimulationModel
from simulation_model.simulation_parameters import SimulationParameters
from simulation_model.timing import FixedTimingFunction, TimeInterval, TimeDensity, ActivityTiming, TimeDensityCalendar, \
    ExponentialTimingFunction


def run_example_1():
    p_source = Place("source", 0, 0, is_initial=True)
    t_register = Transition("t_register", 200, 0)
    p1 = Place("p1", 400, 0)
    t_treat = Transition("t_treat", 600, 0)
    p_sink = Place("sink", 800, 0)
    petri_net = SimplePetriNet(
        places=[
            p_source, p1, p_sink
        ],
        transitions=[
            t_register, t_treat
        ],
        arcs=[
            Arc(p_source, t_register),
            Arc(t_register, p1),
            Arc(p1, t_treat),
            Arc(t_treat, p_sink)
        ],
        labels=LabelingFunction({
            t_register.get_id(): "register patient",
            t_treat.get_id():    "treat patient"
        })
    )
    attr_doctor = CPM_Categorical_Attribute(
        "doctor",
        ["Doc_Aalst", "Doktor_Bibber"])
    #attr_illness = CPM_Categorical_Attribute(
        #"illness",
        #["Bias_Blindness", "Causal_Confusion_Syndrome", "Null_Pointer_Neurosis"])
    attr_treatment_delayed = CPM_Categorical_Attribute(
        "treatment_delayed",
        ["No_Delay", "Slight_Delay", "High_Delay"])
    act_register = CPM_Activity("register patient")
    act_treat = CPM_Activity("treat patient")
    treatment_delayed_valuation = BayesianValuation(
        ValuationParameters([
            ValuationParameter(attr_doctor),
            #ValuationParameter(attr_illness)
        ]),
        attr_treatment_delayed,
        probability_mappings={
            tuple(["Doc_Aalst"]):     {"No_Delay": 0.1, "Slight_Delay": 0.6, "High_Delay": 0.3},
            tuple(["Doktor_Bibber"]): {"No_Delay": 0.5, "Slight_Delay": 0.3, "High_Delay": 0.2},
            #tuple(["Doc_Aalst", "Bias_Blindness"]):                {"No_Delay": 0.1, "Slight_Delay": 0.6, "High_Delay": 0.3},
            #tuple(["Doc_Aalst", "Causal_Confusion_Syndrome"]):     {"No_Delay": 0.0, "Slight_Delay": 0.7, "High_Delay": 0.3},
            #tuple(["Doc_Aalst", "Null_Pointer_Neurosis"]):         {"No_Delay": 0.1, "Slight_Delay": 0.4, "High_Delay": 0.5},
            #tuple(["Doktor_Bibber", "Bias_Blindness"]):            {"No_Delay": 0.5, "Slight_Delay": 0.5, "High_Delay": 0.0},
            #tuple(["Doktor_Bibber", "Causal_Confusion_Syndrome"]): {"No_Delay": 0.1, "Slight_Delay": 0.7, "High_Delay": 0.2},
            #tuple(["Doktor_Bibber", "Null_Pointer_Neurosis"]):     {"No_Delay": 0.4, "Slight_Delay": 0.4, "High_Delay": 0.2},
        }
    )
    causal_structure = CausalProcessStructure(
        attributes=[
            attr_doctor,
            attr_treatment_delayed,
            #attr_illness
        ],
        activities=[
            act_register,
            act_treat
        ],
        attributeActivities=AttributeActivities(amap={
            attr_doctor.get_id(): act_register,
            attr_treatment_delayed.get_id(): act_treat,
            #attr_illness.get_id(): act_register
        }),
        relations=[
            AttributeRelation(attr_doctor, attr_treatment_delayed, is_aggregated=False),
            #AttributeRelation(attr_illness, attr_treatment_delayed, is_aggregated=False)
        ]
    )
    causal_model = CausalProcessModel(
        CS=causal_structure,
        Sagg=AggregationSelections(
            relationsToSelection={}
        ),
        Fagg=AggregationFunctions(
            relationsToAggregation={}
        ),
        V=AttributeValuations(
            attributeIdToValuation={
                "doctor": BayesianValuation(
                    ValuationParameters([]),
                    attr_doctor,
                    probability_mappings={
                        tuple([]): {"Doc_Aalst": 0.3, "Doktor_Bibber": 0.7},
                    }
                ),
                #"illness": BayesianValuation(
                    #ValuationParameters([]),
                    #attr_illness
                #),
                "treatment_delayed": treatment_delayed_valuation
            }
        )
    )
    simulation_parameters = SimulationParameters(
        # how many instances should be simulated in total
        number_of_cases=1000,
        # how much time between cases starting the process
        case_arrival_rate=ExponentialTimingFunction(average_value=TimeInterval(minutes=15),
                                                    maximal_value=TimeInterval(minutes=120),
                                                    function_name="case_arrival"),
        # at what times do cases arrive
        case_arrival_density=TimeDensityCalendar.StandardDensity(),
        # at what times do things happen in the process (i.e., people working)
        service_time_density=TimeDensityCalendar.StandardDensity(),
        # how long executions of specific activities take
        activity_timings=[
            ActivityTiming(activity_name="register patient",
                           execution_delay=ExponentialTimingFunction(average_value=TimeInterval(minutes=5),
                                                                     maximal_value=TimeInterval(minutes=20),
                                                                     function_name="register_patient_delay")),
            ActivityTiming(activity_name="treat patient",
                           execution_delay=ExponentialTimingFunction(average_value=TimeInterval(minutes=20),
                                                                     maximal_value=TimeInterval(minutes=90),
                                                                     function_name="treat_patient_delay")),
        ]

    )
    sim = SimulationModel(petri_net, causal_model, simulation_parameters)
    print(sim.to_string())
    sim.to_CPN()


def run_example_2():
    ot_orders = ObjectType("orders")
    ot_struct = ObjectTypeStructure([ot_orders], [])
    p_source = OCPN_Place("source", 0, 0, object_type=ot_orders, is_initial=True)
    t_place = OCPN_Transition("t_place", 200, 0, leading_type=ot_orders)
    p1 = OCPN_Place("p1", 400, 0, object_type=ot_orders)
    t_ship = OCPN_Transition("t_ship", 600, 0, leading_type=ot_orders)
    p_sink = OCPN_Place("sink", 800, 0, object_type=ot_orders)
    oc_petri_net = ObjectCentricPetriNet(
        places=[
            p_source, p1, p_sink
        ],
        transitions=[
            t_place, t_ship
        ],
        arcs=[
            OCPN_Arc(p_source, t_place),
            OCPN_Arc(t_place, p1),
            OCPN_Arc(p1, t_ship),
            OCPN_Arc(t_ship, p_sink)
        ],
        labels=LabelingFunction({
            t_place.get_id(): "place order",
            t_ship.get_id():  "ship order"
        })
    )


if __name__ == "__main__":
    run_example_2()
    run_example_1()
