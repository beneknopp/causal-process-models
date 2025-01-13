from causal_model.causal_process_model import CausalProcessModel, AggregationSelections, AggregationFunctions, \
    AttributeValuations
from causal_model.causal_process_structure import CausalProcessStructure, AttributeActivities, \
    CPM_Activity, \
    CPM_Categorical_Attribute, CPM_Categorical_Domain
from causal_model.valuation import BayesianValuation, ValuationParameters
from examples.utils import read_initial_marking
from object_centric.object_centric_petri_net import ObjectCentricPetriNet as OCPN, ObjectCentricPetriNetArc as Arc, \
    ObjectCentricPetriNetPlace as Place, ObjectCentricPetriNetTransition as Transition
from object_centric.object_type_structure import ObjectType, ObjectTypeStructure, ObjectTypeRelation, Multiplicity
from process_model.petri_net import LabelingFunction
from simulation_model.simulation_model import SimulationModel
from simulation_model.simulation_parameters import SimulationParameters
from simulation_model.timing import TimeInterval, ActivityTiming, TimeDensityCalendar, \
    ExponentialTimingFunction, FixedTimingFunction


def run_example_order_management_complete(output_path, model_name):
    ot_orders   = ObjectType("orders")
    ot_items    = ObjectType("items")
    ot_packages = ObjectType("packages")
    ot_struct = ObjectTypeStructure([ot_orders, ot_items, ot_packages], [
        ObjectTypeRelation(ot_orders,   Multiplicity.ONE, Multiplicity.MANY, ot_items),
        ObjectTypeRelation(ot_packages, Multiplicity.ONE, Multiplicity.MANY, ot_items)
    ])
    initial_marking = read_initial_marking("./resources/order-management_100.sqlite", ot_struct)

    yo = 800
    yi = -200
    yp = -1200
    ysync = (yo + yi) / 2
    po1 = Place("po1", 0, yo, object_type=ot_orders, is_initial=True)
    pi1 = Place("pi1", 0, yi, object_type=ot_items, is_initial=True)
    pp1 = Place("pp1", 0, yp, object_type=ot_packages, is_initial=True)

    t_place = Transition("tplace", 500, yo, ot_orders)
    t_confirm = Transition("tconfirm", 1000, yo, ot_orders)
    t_remind = Transition("tremind", 1250, yo + 500, ot_orders)
    t_pay = Transition("tpay", 1500, yo, ot_orders)

    t_check = Transition("tcheck", 800, yi - 100, ot_items)
    t_ioos = Transition("tioos", 1000, yi - 200, ot_items)
    t_reorder = Transition("treorder", 1500, yi - 200, ot_items)
    t_skip = Transition("tskip", 1250, yi + 200, ot_items)
    t_pick = Transition("tpick", 2000, yi, ot_items)

    t_create = Transition("tcreate", 2500, yp, ot_packages)
    t_send = Transition("tsend", 3000, yp, ot_packages)
    t_fail = Transition("tfail", 3500, yp, ot_packages)
    t_deliver = Transition("tdeliver", 3500, yp-500, ot_packages)

    po2 = Place("po2", 750, yo, ot_orders)
    po3 = Place("po3", 1250, yo, ot_orders)
    po4 = Place("po4", 1750, yo, ot_orders, is_final=True)

    pi2 = Place("pi2", 750, yi - 150, object_type=ot_items)
    pi3 = Place("pi3", 1000, yi, object_type=ot_items)
    pi4 = Place("pi4", 1250, yi, object_type=ot_items)
    pi5 = Place("pi5", 1500, yi, object_type=ot_items)
    pi6 = Place("pi6", 2250, yi, object_type=ot_items)
    pi7 = Place("pi7", 2750, yi, object_type=ot_items)
    pi8 = Place("pi8", 3250, yi, object_type=ot_items)
    pi9 = Place("pi9", 3750, yi, object_type=ot_items ,is_final=True)

    pp2 = Place("pp2", 2750, yp, ot_packages)
    pp3 = Place("pp3", 3250, yp, ot_packages)
    pp4 = Place("pp4", 3750, yp, ot_packages, is_final=True)

    ocpn = OCPN(
        places=[
            po1, po2, po3, po4,
            pi1, pi2, pi3, pi4, pi5, pi6, pi7, pi8, pi9,
            pp2, pp3, pp4
        ],
        transitions=[
            t_place, t_confirm, t_remind, t_pay,
            t_check, t_ioos, t_reorder, t_skip, t_pick,
            t_create, t_send, t_fail, t_deliver
        ],
        arcs=[
            Arc(po1, t_place), Arc(t_place, po2), Arc(po2, t_confirm), Arc(t_confirm, po3), Arc(po3, t_remind), Arc(t_remind, po3), Arc(po3, t_pay), Arc(t_pay, po4),
            ################################
            Arc(pi1, t_place, True), Arc(t_place, pi2, True), Arc(pi2, t_check), Arc(t_check, pi3),
            Arc(pi3, t_ioos), Arc(pi3, t_skip), Arc(t_ioos, pi4), Arc(pi4, t_reorder), Arc(t_reorder, pi5), Arc(t_skip, pi5), Arc(pi5, t_pick),
            Arc(t_pick, pi6), Arc(pi6, t_create, True), Arc(t_create, pi7, True), Arc(pi7, t_send, True), Arc(t_send, pi8, True),
                Arc(pi8, t_fail, True), Arc(t_fail, pi8, True), Arc(pi8, t_deliver, True), Arc(t_deliver, pi9, True),
            ################################
            Arc(pp1, t_create), Arc(t_create, pp2), Arc(pp2, t_send), Arc(t_send, pp3), Arc(pp3, t_fail), Arc(t_fail, pp3), Arc(pp3, t_deliver), Arc(t_deliver, pp4)
        ],
        labels=LabelingFunction({
            t_place.get_id(): "place order",
            t_confirm.get_id(): "confirm order",
            t_remind.get_id(): "payment reminder",
            t_pay.get_id(): "pay order",
            ################################
            t_check.get_id(): "check stock",
            t_ioos.get_id(): "item out of stock",
            t_reorder.get_id(): "reorder item",
            t_pick.get_id(): "pick item",
            ################################
            t_create.get_id(): "create package",
            t_send.get_id(): "send package",
            t_fail.get_id(): "failed delivery",
            t_deliver.get_id(): "package delivered",

        })
    )
    act_place_order         = CPM_Activity("place order", ot_orders)
    act_confirm_order       = CPM_Activity("confirm order", ot_orders)
    act_payment_reminder    = CPM_Activity("payment reminder", ot_orders)
    act_pay_order           = CPM_Activity("pay order", ot_orders)
    act_check_stock         = CPM_Activity("check stock", ot_items)
    act_item_out_of_stock   = CPM_Activity("item out of stock", ot_items)
    act_reorder_item        = CPM_Activity("reorder item", ot_items)
    act_pick_item           = CPM_Activity("pick item", ot_items)
    act_create_package      = CPM_Activity("create package", ot_packages)
    act_send_package        = CPM_Activity("send package", ot_packages)
    act_failed_delivery     = CPM_Activity("failed delivery", ot_packages)
    act_package_delivered   = CPM_Activity("package delivered", ot_packages)
    activities = {}
    for act in [act_place_order, act_confirm_order, act_payment_reminder, act_pay_order, act_check_stock, act_item_out_of_stock, act_reorder_item,
                act_pick_item, act_create_package, act_send_package, act_failed_delivery, act_package_delivered]:
        activities[act.get_id()] = act
    dummy_attributes = {}
    amap = {}
    attributeToValuation = {}
    activity_timings = {
        act_place_order: ActivityTiming(act_place_order.get_name(), FixedTimingFunction(TimeInterval(seconds=1))),
        act_check_stock: ActivityTiming(act_check_stock.get_name(), ExponentialTimingFunction(
                                        average_value=TimeInterval(days=2),
                                        maximal_value=TimeInterval(days=10))),
        act_item_out_of_stock: ActivityTiming(act_item_out_of_stock.get_name(), ExponentialTimingFunction(
            average_value=TimeInterval(days=2),
            maximal_value=TimeInterval(days=10))),
        act_reorder_item: ActivityTiming(act_reorder_item.get_name(), ExponentialTimingFunction(
            average_value=TimeInterval(days=10),
            maximal_value=TimeInterval(days=40))),
    }
    for act in activities.values():
        dummy_attribute_id = "{0}_happened".format(act.get_id())
        label1 = "Yes_{0}".format(act.get_id())
        label2 = "No_{0}".format(act.get_id())
        dummy_attribute = CPM_Categorical_Attribute(CPM_Categorical_Domain([label1, label2], dummy_attribute_id), dummy_attribute_id)
        dummy_attributes[dummy_attribute_id] = dummy_attribute
        amap[dummy_attribute] = act
        attributeToValuation[dummy_attribute] = BayesianValuation(
            ValuationParameters([]), dummy_attribute, probability_mappings={(): {label1: 0.8, label2: 0.2}, })
        if act not in activity_timings:
            activity_timing = ActivityTiming(
                activity_name=act.get_name(),
                execution_delay=ExponentialTimingFunction(average_value=TimeInterval(hours=1),
                maximal_value=TimeInterval(hours=3))
            )
            activity_timings[act] = activity_timing
    causal_structure = CausalProcessStructure(
        event_attributes=list(dummy_attributes.values()),
        case_attributes=[],
        activities=list(activities.values()),
        attributeActivities=AttributeActivities(amap=amap),
        relations=[]
    )
    causal_model = CausalProcessModel(
        CS=causal_structure,
        Sagg=AggregationSelections(relationsToSelection={}),
        Fagg=AggregationFunctions(relationsToAggregation={}),
        V=AttributeValuations(attributeToValuation=attributeToValuation)
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
        activity_timings=list(activity_timings.values())
    )
    sim = SimulationModel(ocpn, causal_model, ot_struct, simulation_parameters)
    if initial_marking is not None:
        sim.set_initial_marking(initial_marking)

    print(sim.to_string())

    sim.to_CPN(output_path, model_name)