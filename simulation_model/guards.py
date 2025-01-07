from simulation_model.cpn_utils.cpn_transition import CPN_Transition

'''
fun guard_place_order(x: C_orders, ys: C_items_LIST)= 
let 
val items_complete = extract_items_by_ids(ys, (#2 x)) 
val products_complete = extract_products_by_ids(ys, (#2 x)) 
in 
items_complete, products_complete
end;
'''

class GuardAndCodeManager:

    def __init__(self):
        self.guards_by_transitions = {}
        self.code_by_transitions = {}

    def add_transition(self, transition: CPN_Transition):
        self.guards_by_transitions[transition] = []
