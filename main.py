from causal_model.CausalProcessModel import CausalProcessModel, AggregationSelections, AggregationFunctions, \
    AttributeValuation, AttributeValuations
from causal_model.CausalProcessStructure import CausalProcessStructure, AttributeActivities, CPM_Attribute, \
    CPM_Activity, \
    AttributeRelation, CPM_Categorical_Attribute
from causal_model.Valuation import BayesianValuation, ValuationParameters, ValuationParameter
from process_model.PetriNet import PetriNet, LabelingFunction, \
    SimplePetriNetPlace as Place, SimplePetriNetTransition as Transition, SimplePetriNetArc as Arc
from simulation_model.SimulationModel import SimulationModel

def run_example_1():
    p_source = Place("source", 0, 0, is_initial=True)
    t_register = Transition("t_register", 200, 0)
    p1 = Place("p1", 400, 0)
    t_treat = Transition("t_treat", 600, 0)
    p_sink = Place("sink", 800, 0)
    petri_net = PetriNet(
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
    attr_doctor             = CPM_Categorical_Attribute(
        "doctor",
        ["Doc Aalst", "Doktor Bibber"])
    attr_weekday             = CPM_Categorical_Attribute(
        "weekday",
        ["Monday", "Tuesday", "Wednesday"])
    attr_treatment_delayed  = CPM_Categorical_Attribute(
        "treatment_delayed",
        ["No Delay", "Slight Delay", "High Delay"])
    act_register       = CPM_Activity("register patient")
    act_treat          = CPM_Activity("treat patient")
    treatment_delayed_valuation = BayesianValuation(
        ValuationParameters([
            ValuationParameter(attr_doctor),
            ValuationParameter(attr_weekday)
        ]),
        attr_treatment_delayed
    )
    s = treatment_delayed_valuation.to_SML()
    print(s)
    causal_structure = CausalProcessStructure(
        attributes=[
            attr_doctor,
            attr_treatment_delayed,
            attr_weekday
        ],
        activities=[
            act_register,
            act_treat
        ],
        attributeActivities=AttributeActivities(amap={
            attr_doctor.get_id(): act_register,
            attr_treatment_delayed.get_id(): act_treat,
            attr_weekday.get_id(): act_register
        }),
        relations=[
            AttributeRelation(attr_doctor, attr_treatment_delayed, is_aggregated=False)
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
                "weekday": BayesianValuation(
                    ValuationParameters([]),
                    attr_weekday
                ),
                "treatment_delayed": treatment_delayed_valuation
            }
        )
    )
    initial_marking_case_ids = ["c1", "c2"]
    sim = SimulationModel(petri_net, causal_model, initial_marking_case_ids)
    print(sim.to_string())
    sim.to_CPN()


if __name__ == "__main__":
    run_example_1()
