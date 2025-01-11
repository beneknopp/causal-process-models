from causal_model.aggregation_selections.selection_functions import SelectionBy_toManyRelationsLastObservation
from causal_model.causal_process_model import CausalProcessModel, AggregationSelections, AggregationFunctions, \
    AttributeValuations, AggregationFunction
from causal_model.causal_process_structure import CausalProcessStructure, AttributeActivities, \
    CPM_Activity, \
    AttributeRelation, CPM_Categorical_Attribute, CPM_EventStartTime_Attribute, \
    CPM_EventCompleteTime_Attribute, CPM_Categorical_Domain, REAL_DOMAIN
from causal_model.valuation import BayesianValuation, ValuationParameters, ValuationParameter
from object_centric.object_centric_petri_net import ObjectCentricPetriNet as OCPN, ObjectCentricPetriNetArc as Arc, \
    ObjectCentricPetriNetPlace as Place, ObjectCentricPetriNetTransition as Transition
from object_centric.object_type_structure import ObjectType, ObjectTypeStructure, ObjectTypeRelation, Multiplicity
from process_model.petri_net import LabelingFunction
from simulation_model.simulation_model import SimulationModel
from simulation_model.simulation_parameters import SimulationParameters
from simulation_model.timing import TimeInterval, ActivityTiming, TimeDensityCalendar, \
    ExponentialTimingFunction


def run_example_1(output_path, model_name):
    p_source = Place("source", 0, 0, is_initial=True)
    t_register = Transition("t_register", 600, 0)
    p1 = Place("p1", 1200, 0)
    t_treat = Transition("t_treat", 1600, 0)
    p_sink = Place("sink", 2400, 0, is_final=True)
    petri_net = OCPN(
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
            ("Dr_Yuan",): {"No_Delay": 0.5, "Slight_Delay": 0.0, "High_Delay": 0.5},
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
        case_arrival_rate=ExponentialTimingFunction(average_value=TimeInterval(minutes=5),
                                                    maximal_value=TimeInterval(minutes=15),
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
                           execution_delay=ExponentialTimingFunction(average_value=TimeInterval(minutes=30),
                                                                     maximal_value=TimeInterval(minutes=120),
                                                                     function_name="treat_patient_delay")),
        ]

    )
    object_type_structure = ObjectTypeStructure()
    sim = SimulationModel(petri_net, causal_model, object_type_structure, simulation_parameters)
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
    petri_net = OCPN(
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
            t_treat.get_id(): "treat patient",
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
            ("Dr_Yuan",): {"No_Delay": 0.7, "High_Delay": 0.3},
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
            ("Dr_Yuan", "No_Delay"): {"Happy": 1.0, "Mad": 0.0},
            ("Dr_Knopp", "No_Delay"): {"Happy": 0.9, "Mad": 0.1},
            ("Dr_Yuan", "High_Delay"): {"Happy": 0.7, "Mad": 0.3},
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


def run_example_oc_simple(output_path, model_name):
    ot_orders = ObjectType("orders")
    ot_items = ObjectType("items")
    ot_struct = ObjectTypeStructure([ot_orders, ot_items], [
        ObjectTypeRelation(ot_orders, Multiplicity.ONE, Multiplicity.MANY, ot_items)
    ])
    yo = 400
    yi = 200
    ysync = (yo + yi) / 2
    po1 = Place("po1", 0, yo, object_type=ot_orders, is_initial=True)
    pi1 = Place("pi1", 0, yi, object_type=ot_items, is_initial=True)
    to1 = Transition("to1", 400, yo, leading_type=ot_orders)
    ti1 = Transition("ti1", 400, yi, leading_type=ot_items)
    po2 = Place("po2", 800, yo, object_type=ot_orders)
    pi2 = Place("pi2", 800, yi, object_type=ot_items)
    tsync = Transition("tsync", 1200, ysync, leading_type=ot_orders)
    po3 = Place("po3", 1600, yo, object_type=ot_orders, is_final=True)
    pi3 = Place("pi3", 1600, yi, object_type=ot_items, is_final=True)
    ocpn = OCPN(
        places=[
            po1, pi1, po2, pi2, po3, pi3
        ],
        transitions=[
            to1, ti1, tsync
        ],
        arcs=[
            Arc(po1, to1),
            Arc(pi1, ti1),
            Arc(to1, po2),
            Arc(ti1, pi2),
            Arc(po2, tsync),
            Arc(pi2, tsync, is_variable=True),
            Arc(tsync, po3),
            Arc(tsync, pi3, is_variable=True),
        ],
        labels=LabelingFunction({
            tsync.get_id(): "place order"
        })
    )
    attr_priority = CPM_Categorical_Attribute(
        "priority",
        ["Prio_High", "Prio_Low"])
    act_place_order = CPM_Activity("place order", leading_type=ot_orders)
    priority_valuation = BayesianValuation(
        ValuationParameters([]),
        attr_priority,
        probability_mappings={
            (): {"Prio_High": 0.1, "Prio_Low": 0.9},
        }
    )
    causal_structure = CausalProcessStructure(
        attributes=[
            attr_priority
        ],
        activities=[
            act_place_order
        ],
        attributeActivities=AttributeActivities(amap={
            attr_priority.get_id(): act_place_order
        }),
        relations=[]
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
                "priority": priority_valuation
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
            ActivityTiming(activity_name="place order",
                           execution_delay=ExponentialTimingFunction(average_value=TimeInterval(minutes=5),
                                                                     maximal_value=TimeInterval(minutes=20)))
        ]

    )
    sim = SimulationModel(ocpn, causal_model, ot_struct, simulation_parameters)
    print(sim.to_string())
    sim.to_CPN(output_path, model_name)


def run_example_oc_complex(output_path, model_name):
    ot_orders = ObjectType("orders")
    ot_items = ObjectType("items")
    ot_struct = ObjectTypeStructure([ot_orders, ot_items], [
        ObjectTypeRelation(ot_orders, Multiplicity.ONE, Multiplicity.MANY, ot_items)
    ])
    yo = 400
    yi = 200
    ysync = (yo + yi) / 2
    po1 = Place("po1", 0, yo, object_type=ot_orders, is_initial=True)
    pi1 = Place("pi1", 0, yi, object_type=ot_items, is_initial=True)
    to1 = Transition("to1", 400, yo, leading_type=ot_orders)
    ti1 = Transition("ti1", 400, yi, leading_type=ot_items)
    po2 = Place("po2", 800, yo, object_type=ot_orders)
    pi2 = Place("pi2", 800, yi, object_type=ot_items)
    tplace = Transition("tplace", 1200, ysync, leading_type=ot_orders)
    po3 = Place("po3", 1600, yo, object_type=ot_orders)
    pi3 = Place("pi3", 1600, yi, object_type=ot_items)
    tpick = Transition("tpick", 2000, ysync, leading_type=ot_items)
    pi4 = Place("pi4", 2400, yi, object_type=ot_items)
    tship = Transition("tship", 2400, ysync, leading_type=ot_orders)
    pofin = Place("pofin", 2800, yo, object_type=ot_orders, is_final=True)
    pifin = Place("pifin", 2800, yi, object_type=ot_items, is_final=True)

    ocpn = OCPN(
        places=[
            po1, pi1, po2, pi2, po3, pi3, pi4, pofin, pifin
        ],
        transitions=[
            to1, ti1, tplace, tpick, tship
        ],
        arcs=[
            Arc(po1, to1),
            Arc(pi1, ti1),
            Arc(to1, po2),
            Arc(ti1, pi2),
            Arc(po2, tplace),
            Arc(pi2, tplace, is_variable=True),
            Arc(tplace, po3),
            Arc(tplace, pi3, is_variable=True),
            Arc(pi3, tpick),
            Arc(po3, tpick),
            Arc(tpick, po3),
            Arc(tpick, pi4),
            Arc(po3, tship),
            Arc(pi4, tship, is_variable=True),
            Arc(tship, pofin),
            Arc(tship, pifin, is_variable=True),
        ],
        labels=LabelingFunction({
            tplace.get_id(): "place order",
            tpick.get_id(): "pick item",
            tship.get_id(): "ship order"
        })
    )
    act_place_order = CPM_Activity("place order", leading_type=ot_orders)
    act_pick_item = CPM_Activity("pick item", leading_type=ot_items)
    act_ship_order = CPM_Activity("ship order", leading_type=ot_orders)
    attr_place_order_completetime = CPM_EventCompleteTime_Attribute(act_place_order.get_id())
    attr_ship_order_performance = CPM_Categorical_Attribute("ship_order_performance", ["Goood", "Baaad"])
    ship_order_performance_valuation = BayesianValuation(
        ValuationParameters([
            ValuationParameter(attr_place_order_completetime)
        ]), attr_ship_order_performance,
        probability_mappings={
            (): {"Baaad": 0.2, "Goood": 0.8}, })
    causal_structure = CausalProcessStructure(
        event_attributes=[
            attr_place_order_completetime,
            attr_ship_order_performance
        ],
        case_attributes=[],
        activities=[
            act_place_order,
            act_pick_item,
            act_ship_order
        ],
        attributeActivities=AttributeActivities(amap={
            attr_place_order_completetime: act_place_order,
            attr_ship_order_performance: act_ship_order
        }),
        relations=[
            AttributeRelation(attr_place_order_completetime, attr_ship_order_performance)
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
            attributeToValuation={
                attr_ship_order_performance: ship_order_performance_valuation
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
            ActivityTiming(activity_name="place order",
                           execution_delay=ExponentialTimingFunction(average_value=TimeInterval(minutes=5),
                                                                     maximal_value=TimeInterval(minutes=20))),
            ActivityTiming(activity_name="pick item",
                           execution_delay=ExponentialTimingFunction(average_value=TimeInterval(hours=1),
                                                                     maximal_value=TimeInterval(hours=3))),
            ActivityTiming(activity_name="ship order",
                           execution_delay=ExponentialTimingFunction(average_value=TimeInterval(days=3),
                                                                     maximal_value=TimeInterval(days=5), )),
        ]
    )
    sim = SimulationModel(ocpn, causal_model, ot_struct, simulation_parameters)
    print(sim.to_string())
    sim.to_CPN(output_path, model_name)


def run_example_oc_aggregations(output_path, model_name):
    ot_orders = ObjectType("orders")
    ot_items = ObjectType("items")
    ot_struct = ObjectTypeStructure([ot_orders, ot_items], [
        ObjectTypeRelation(ot_orders, Multiplicity.ONE, Multiplicity.MANY, ot_items)
    ])
    yo = 800
    yi = -200
    ysync = (yo + yi) / 2
    po3 = Place("po3", 0, yo, object_type=ot_orders, is_initial=True)
    pi3 = Place("pi3", 0, yi, object_type=ot_items, is_initial=True)
    tpick = Transition("tpick", 600, ysync, leading_type=ot_items)
    pi4 = Place("pi4", 1200, yi, object_type=ot_items)
    tship = Transition("tship", 1200, ysync, leading_type=ot_orders)
    pofin = Place("pofin", 1600, yo, object_type=ot_orders, is_final=True)
    pifin = Place("pifin", 1600, yi, object_type=ot_items, is_final=True)

    ocpn = OCPN(
        places=[
            po3, pi3, pi4, pofin, pifin
        ],
        transitions=[
            tpick, tship
        ],
        arcs=[
            Arc(pi3, tpick),
            Arc(po3, tpick),
            Arc(tpick, po3),
            Arc(tpick, pi4),
            Arc(po3, tship),
            Arc(pi4, tship, is_variable=True),
            Arc(tship, pofin),
            Arc(tship, pifin, is_variable=True),
        ],
        labels=LabelingFunction({
            tpick.get_id(): "pick item",
            tship.get_id(): "ship order"
        })
    )
    act_pick_item   = CPM_Activity("pick item", leading_type=ot_items)
    act_ship_order  = CPM_Activity("ship order", leading_type=ot_orders)
    attr_pick_item_starttime    = CPM_EventStartTime_Attribute(act_pick_item.get_id())
    attr_pick_item_completetime = CPM_EventCompleteTime_Attribute(act_pick_item.get_id())
    attr_logistics_service_provider = CPM_Categorical_Attribute(
        CPM_Categorical_Domain(["RapidGmbH", "DHL"], "logistics_service_provider"),
        "logistics_service_provider",
        )
    attr_lagged_batch_processing = CPM_Categorical_Attribute(
        CPM_Categorical_Domain(["NotLagged", "Lagged"], "lagged_batch_processing"),
        "lagged_batch_processing",
    )
    logistics_service_provider_valuation = BayesianValuation(
        ValuationParameters([]), attr_logistics_service_provider,
        probability_mappings={
            (): {"RapidGmbH": 0.2, "DHL": 0.8}, })
    r_pick_item_completetime_TO_lagged_batch_processing = AttributeRelation(attr_pick_item_completetime,
                                                                         attr_lagged_batch_processing,
                                                                         is_aggregated=True)
    causal_structure = CausalProcessStructure(
        event_attributes=[
            attr_pick_item_starttime,
            attr_pick_item_completetime,
            attr_logistics_service_provider,
            attr_lagged_batch_processing
        ],
        case_attributes=[],
        activities=[
            act_pick_item,
            act_ship_order
        ],
        attributeActivities=AttributeActivities(amap={
            attr_pick_item_starttime: act_pick_item,
            attr_pick_item_completetime: act_pick_item,
            attr_logistics_service_provider: act_ship_order,
            attr_lagged_batch_processing: act_ship_order,
        }),
        relations=[
            r_pick_item_completetime_TO_lagged_batch_processing
        ]
    )
    causal_model = CausalProcessModel(
        CS=causal_structure,
        Sagg=AggregationSelections(
            relationsToSelection={
                r_pick_item_completetime_TO_lagged_batch_processing: SelectionBy_toManyRelationsLastObservation(
                    "select_pick_times_by_order_item_relation",
                    r_pick_item_completetime_TO_lagged_batch_processing
                )
            }
        ),
        Fagg=AggregationFunctions(
            relationsToAggregation={
                r_pick_item_completetime_TO_lagged_batch_processing: AggregationFunction(
                    r_pick_item_completetime_TO_lagged_batch_processing, REAL_DOMAIN)
            }
        ),
        V=AttributeValuations(
            attributeToValuation={
                attr_logistics_service_provider: logistics_service_provider_valuation,
                attr_lagged_batch_processing: BayesianValuation(ValuationParameters([]), attr_lagged_batch_processing)
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
            ActivityTiming(activity_name="pick item",
                           execution_delay=ExponentialTimingFunction(average_value=TimeInterval(hours=1),
                                                                     maximal_value=TimeInterval(hours=3))),
            ActivityTiming(activity_name="ship order",
                           execution_delay=ExponentialTimingFunction(average_value=TimeInterval(days=3),
                                                                     maximal_value=TimeInterval(days=5), )),
        ]
    )
    sim = SimulationModel(ocpn, causal_model, ot_struct, simulation_parameters)
    print(sim.to_string())
    sim.to_CPN(output_path, model_name)


if __name__ == "__main__":
    output_path = "output"
    model_name_1 = "collider_simple"
    model_name_2 = "confounder_simple"
    model_name_oc_simple = "object_centric_simple"
    model_name_oc_complex = "object_centric_complex"
    model_name_oc_aggregations = "object_centric_aggregations"
    # run_example_1(output_path, model_name_1)
    # run_example_2(output_path, model_name_2)
    # run_example_oc_simple(output_path,  model_name_oc_simple)
    #run_example_oc_complex(output_path, model_name_oc_complex)
    run_example_oc_aggregations(output_path, model_name_oc_aggregations)
