from causal_model.CausalProcessModel import CausalProcessModel, AggregationSelection, AggregationFunction, \
    AttributeValuation
from causal_model.CausalProcessStructure import CausalProcessStructure, AttributeActivities, Attribute, Activity, \
    AttributeRelation
from process_model.PetriNet import PetriNet, LabelingFunction, Place, Transition, Arc
from simulation_model.SimulationModel import SimulationModel

if __name__ == "__main__":
    p_source = Place("source")
    p1 = Place("p1")
    p_sink = Place("sink")
    t_register = Transition("t_register")
    t_treat = Transition("t_treat")
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
    attr_doctor             = Attribute("doctor")
    attr_treatment_delayed  = Attribute("treatment_delayed")
    act_register       = Activity("register patient")
    act_treat          = Activity("treat patient")
    causal_structure = CausalProcessStructure(
        attributes=[
            attr_doctor,
            attr_treatment_delayed
        ],
        activities=[
            act_register,
            act_treat
        ],
        attributeActivites=AttributeActivities(amap={
            attr_doctor: act_register,
            attr_treatment_delayed: act_treat
        }),
        relations=[
            AttributeRelation(attr_doctor, attr_treatment_delayed, is_aggregated=False)
        ]
    )
    causal_model = CausalProcessModel(
        CS=causal_structure,
        Sagg=AggregationSelection(
            relationsToSelection={}
        ),
        Fagg=AggregationFunction(
            relationsToAggregation={}
        ),
        V=AttributeValuation(
            attributeToValuation={}
        )
    )
    sim = SimulationModel(petri_net, causal_model)
    print(sim.to_string())
    sim.to_CPN()
