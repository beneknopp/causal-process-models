from causal_model import CausalProcessModel
from process_model.PetriNet import PetriNet
from simulation_model.CPM_CPN_Converter import CPM_CPN_Converter
from utils.validators import validate_condition


class SimulationModel:

    def __validate(self):
        petri_net_activities = self.__petriNet.get_activities()
        causal_model_activities = self.__causalModel.get_activity_names()
        validate_condition(all(
            act in petri_net_activities
            for act in causal_model_activities))

    def __init__(self,
                 petriNet: PetriNet,
                 causalModel: CausalProcessModel,
                 initial_marking_case_ids):
        self.__petriNet = petriNet
        self.__causalModel = causalModel
        self.initial_marking_case_ids = initial_marking_case_ids
        self.__validate()


    def to_string(self):
        s = ""
        s += "petri net: \n"
        s += self.__petriNet.to_string()
        s += "\ncausal model: \n"
        s += self.__causalModel.to_string()
        petri_net_activities = self.__petriNet.get_activities()
        causal_model_activities = self.__causalModel.get_activity_names()
        s += "Petri net has {0} activities, ".format(str(len(petri_net_activities)))
        s += "Causal Model has {0} activities, ".format(str(len(causal_model_activities)))
        s += "{0} of them are shared.".format(str(len([
            act for act in petri_net_activities if act in causal_model_activities
        ])))
        return s

    def to_CPN(self):
        # create colorsets
        cpn_template_path = "resources/empty.cpn"
        cpn_output_path = "output/simulation_model.cpn"
        converter = CPM_CPN_Converter(cpn_template_path, petriNet=self.__petriNet, causalModel=self.__causalModel,
                                      initial_marking_case_ids=self.initial_marking_case_ids)
        converter.convert()
        converter.export(cpn_output_path)
