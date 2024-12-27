import xml.etree.ElementTree as ET

from causal_model.CausalProcessModel import CausalProcessModel
from process_model.PetriNet import PetriNet
from simulation_model.CPN import CPN
from simulation_model.Colset import ColsetManager


class CPM_CPN_Converter:

    def __init__(self,
                 petriNet: PetriNet,
                 causalModel: CausalProcessModel
                 ):
        cpn_template_path = "../resources/empty.cpn"
        self.tree = ET.parse(cpn_template_path)
        self.root = self.tree.getroot()
        self.mainpage = self.root.find("cpnet").find("page")
        self.subpages = []
        # self.portsock_map = dict()
        self.cpn = CPN(open(cpn_template_path).read())
        self.colset_manager = ColsetManager(self.cpn)
        self.initial_places = {}
        self.new_colsets = []
        self.event_places_by_activity_name = dict()
        self.schema_generation_functions = dict()
        self.transition_substitutions = dict()
        self.port_sock_map = dict()
        self.other_functions = []
        self.uses = []
        self.petriNet = petriNet
        self.causalModel = causalModel

    def convert(self):
        self.__initialize_activities_and_attributes()
        self.__make_colsets()

    def __initialize_activities_and_attributes(self):
        self.__activities = self.causalModel.get_activities()
        self.__attributes = self.causalModel.get_attributes()
        self.__attributeActivities = self.causalModel.get_attribute_activities()
        self.__expand_empty_activities()

    def __expand_empty_activities(self):
        """
        there may be labels in the Petri net that are not described in the causal model
        add an activity without attributes for those
        :return: the complete list of activities after expansion
        """
        petri_net = self.petriNet
        causal_model = self.causalModel
        pn_labels = petri_net.get_activities()
        cm_acts = causal_model.get_activities()
        cm_labels = [act.get_name() for act in cm_acts]
        new_labels = set([l for l in pn_labels if l not in cm_labels])
        for l in new_labels:
            causal_model.add_activity(activity_name=l, activity_id=l)
        all_acts = causal_model.get_activities()
        return all_acts

    def __make_colsets(self):
        activity_ids = [act.get_id() for act in self.__activities]
        attribute_ids = [attr.get_id() for attr in self.__attributes]
        attributes_with_last_observations = self.causalModel.get_attributes_with_non_aggregated_dependencies()
        attributes_with_system_aggregations = self.causalModel.get_attributes_with_aggregated_dependencies()
        self.colset_manager.add_activity_and_attribute_colsets(
            activity_ids=activity_ids,
            attribute_ids=attribute_ids,
            attribute_activities=self.__attributeActivities,
            attributes_with_last_observations=attributes_with_last_observations,
            attributes_with_system_aggregations=attributes_with_system_aggregations
        )