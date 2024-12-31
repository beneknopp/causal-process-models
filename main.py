from causal_model.causal_process_model import CausalProcessModel, AggregationSelections, AggregationFunctions, \
    AttributeValuations
from causal_model.causal_process_structure import CausalProcessStructure, AttributeActivities, \
    CPM_Activity, \
    AttributeRelation, CPM_Categorical_Attribute
from causal_model.valuation import BayesianValuation, ValuationParameters, ValuationParameter
from process_model.petri_net import SimplePetriNet, LabelingFunction, \
    SimplePetriNetPlace as Place, SimplePetriNetTransition as Transition, SimplePetriNetArc as Arc
from simulation_model.simulation_model import SimulationModel
from simulation_model.simulation_parameters import SimulationParameters
from simulation_model.timing import FixedTimingFunction, TimeInterval, TimeDensity, ActivityTiming


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
            ValuationParameter(attr_illness)
        ]),
        attr_treatment_delayed
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
            AttributeRelation(attr_illness, attr_treatment_delayed, is_aggregated=False)
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
        number_of_cases=100,
        # how much time between cases starting the process
        case_arrival_rate=FixedTimingFunction(TimeInterval(hours=1)),
        # at what times do cases arrive
        case_arrival_density=TimeDensity.StandardDensity(),
        # at what times do things happen in the process (i.e., people working)
        service_time_density=TimeDensity.StandardDensity(),
        # how long executions of specific activities take
        activity_timings=[
            ActivityTiming(activity_name="register patient",
                           execution_delay=FixedTimingFunction(TimeInterval(minutes=10))),
            ActivityTiming(activity_name="treat patient",
                           execution_delay=FixedTimingFunction(TimeInterval(hours=2))),
        ]

    )
    sim = SimulationModel(petri_net, causal_model, simulation_parameters)
    print(sim.to_string())
    sim.to_CPN()


if __name__ == "__main__":
    run_example_1()
