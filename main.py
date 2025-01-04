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
from simulation_model.timing import TimeInterval, ActivityTiming, TimeDensityCalendar, \
    ExponentialTimingFunction


def run_example_1(output_path, model_name):
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
            t_treat.get_id(): "treat patient"
        })
    )
    attr_doctor = CPM_Categorical_Attribute(
        "doctor",
        ["Dr_Knopp", "Dr_Yuan"])
    attr_illness = CPM_Categorical_Attribute(
        "illness",
        ["Bias_Blindness", "Causal_Confusion_Syndrome", "Null_Pointer_Neurosis"])
    attr_treatment_delayed = CPM_Categorical_Attribute(
        "treatment_delayed",
        ["No_Delay", "Slight_Delay", "High_Delay"])
    act_register = CPM_Activity("register patient")
    act_treat = CPM_Activity("treat patient")
    treatment_delayed_valuation = BayesianValuation(
        ValuationParameters([
            ValuationParameter(attr_doctor),
            # ValuationParameter(attr_illness)
        ]),
        attr_treatment_delayed,
        probability_mappings={
            ("Dr_Knopp",): {"No_Delay": 0.1, "Slight_Delay": 0.1, "High_Delay": 0.8},
            ("Dr_Yuan",):  {"No_Delay": 0.5, "Slight_Delay": 0.0, "High_Delay": 0.5},
        }
    )
    causal_structure = CausalProcessStructure(
        attributes=[
            attr_doctor,
            attr_treatment_delayed,
            attr_illness
        ],
        activities=[
            act_register,
            act_treat
        ],
        attributeActivities=AttributeActivities(amap={
            attr_doctor.get_id(): act_register,
            attr_treatment_delayed.get_id(): act_treat,
            attr_illness.get_id(): act_register
        }),
        relations=[
            AttributeRelation(attr_doctor, attr_treatment_delayed, is_aggregated=False),
            # AttributeRelation(attr_illness, attr_treatment_delayed, is_aggregated=False)
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
                    attr_doctor
                ),
                "illness": BayesianValuation(
                    ValuationParameters([]),
                    attr_illness
                ),
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
    sim.to_CPN(output_path, model_name)


def run_example_2(output_path, model_name):
    p_source = Place("source", 0, 0, is_initial=True)
    t_register = Transition("t_register", 200, 0)
    p_pre_treat = Place("p_pre_treat", 400, 0)
    p_pre_bill = Place("p_pre_bill", 400, 300)
    t_treat = Transition("t_treat", 600, 0)
    p_post_treat = Place("p_post_treat", 800, 0)
    t_bill = Transition("t_bill", 600, 300)
    p_post_bill = Place("p_post_bill", 800, 300)
    t_complete = Transition("t_complete", 900, 0)
    p_sink = Place("sink", 1200, 0)
    petri_net = SimplePetriNet(
        places=[
            p_source, p_pre_treat, p_pre_bill, p_post_treat, p_post_bill, p_sink
        ],
        transitions=[
            t_register, t_treat, t_bill, t_complete
        ],
        arcs=[
            Arc(p_source, t_register),
            Arc(t_register, p_pre_treat),
            Arc(t_register, p_pre_bill),
            Arc(p_pre_treat, t_treat),
            Arc(p_pre_bill, t_bill),
            Arc(t_treat, p_post_treat),
            Arc(t_bill, p_post_bill),
            Arc(p_post_treat, t_complete),
            Arc(p_post_bill, t_complete),
            Arc(t_complete, p_sink)
        ],
        labels=LabelingFunction({
            t_register.get_id(): "register patient",
            t_treat.get_id():    "treat patient",
            t_bill.get_id(): "send bill",
            t_complete.get_id(): "complete treatment",
        })
    )
    attr_doctor = CPM_Categorical_Attribute(
        "doctor",
        ["Dr_Knopp", "Dr_Yuan"])
    attr_treatment_delayed = CPM_Categorical_Attribute(
        "treatment_delayed",
        ["No_Delay", "High_Delay"])
    attr_costs = CPM_Categorical_Attribute(
        "costs",
        ["High_Costs", "Low_Costs"])
    attr_outcome = CPM_Categorical_Attribute(
        "patient_satisfaction",
        ["Happy", "Mad"])
    act_register = CPM_Activity("register patient")
    act_treat = CPM_Activity("treat patient")
    act_bill = CPM_Activity("send bill")
    act_complete = CPM_Activity("complete treatment")
    treatment_delayed_valuation = BayesianValuation(
        ValuationParameters([
            ValuationParameter(attr_doctor)
        ]),
        attr_treatment_delayed,
        probability_mappings={
            ("Dr_Knopp",): {"No_Delay": 0.2, "High_Delay": 0.8},
            ("Dr_Yuan",):  {"No_Delay": 0.7, "High_Delay": 0.3},
        }
    )
    costs_valuation = BayesianValuation(
        ValuationParameters([]),
        attr_costs,
        probability_mappings={
            (): {"High_Costs": 1.0, "Low_Costs": 0.0},
        }
    )
    outcome_valuation = BayesianValuation(
        ValuationParameters([ValuationParameter(attr_doctor), ValuationParameter(attr_treatment_delayed)]),
        attr_outcome,
        probability_mappings={
            ("Dr_Yuan", "No_Delay"):    {"Happy": 1.0, "Mad": 0.0},
            ("Dr_Knopp", "No_Delay"):   {"Happy": 0.9, "Mad": 0.1},
            ("Dr_Yuan", "High_Delay"):  {"Happy": 0.7, "Mad": 0.3},
            ("Dr_Knopp", "High_Delay"): {"Happy": 0.6, "Mad": 0.4},
        }
    )
    causal_structure = CausalProcessStructure(
        attributes=[
            attr_doctor,
            attr_treatment_delayed,
            attr_costs,
            attr_outcome
        ],
        activities=[
            act_register,
            act_treat,
            act_bill,
            act_complete
        ],
        attributeActivities=AttributeActivities(amap={
            attr_doctor.get_id(): act_register,
            attr_treatment_delayed.get_id(): act_treat,
            attr_costs.get_id(): act_bill,
            attr_outcome.get_id(): act_complete,
        }),
        relations=[
            AttributeRelation(attr_doctor, attr_treatment_delayed),
            AttributeRelation(attr_doctor, attr_outcome),
            AttributeRelation(attr_treatment_delayed, attr_outcome),
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
                "doctor": BayesianValuation(ValuationParameters([]), attr_doctor),
                "treatment_delayed": treatment_delayed_valuation,
                "costs": costs_valuation,
                "patient_satisfaction": outcome_valuation
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
            ActivityTiming(activity_name="send bill",
                           execution_delay=ExponentialTimingFunction(average_value=TimeInterval(hours=1),
                                                                     maximal_value=TimeInterval(days=5),
                                                                     function_name="send_bill_delay")),
            ActivityTiming(activity_name="complete treatment",
                           execution_delay=ExponentialTimingFunction(average_value=TimeInterval(minutes=5),
                                                                     maximal_value=TimeInterval(minutes=10),
                                                                     function_name="complete_treatment_delay")),
        ]

    )
    sim = SimulationModel(petri_net, causal_model, simulation_parameters)
    print(sim.to_string())
    sim.to_CPN(output_path, model_name)

def run_example_oc():
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
    output_path = "output"
    model_name_1 = "collider_simple"
    model_name_2 = "confounder_simple"
    run_example_1(output_path, model_name_1)
    run_example_2(output_path, model_name_2)
