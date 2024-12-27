from causal_model import CausalProcessModel
from process_model.PetriNet import PetriNet
from simulation_model.CPM_CPN_Converter import CPM_CPN_Converter


class SimulationModel:

    def __init__(self,
                 petriNet: PetriNet,
                 causalModel: CausalProcessModel):
        self.__petriNet = petriNet
        self.__causalModel = causalModel

    def to_string(self):
        s = ""
        s += "petri net: \n"
        s += self.__petriNet.to_string()
        s += "\ncausal model: \n"
        s += self.__causalModel.to_string()
        petri_net_activities = self.__petriNet.get_activities()
        causal_model_activities = self.__causalModel.get_activities()
        s += "Petri net has {0} activities, ".format(str(len(petri_net_activities)))
        s += "Causal Model has {0} activities, ".format(str(len(causal_model_activities)))
        s += "{0} of them are shared.".format(str(len([
            act for act in petri_net_activities if act in causal_model_activities
        ])))
        return s

    def to_CPN(self):
        # create colorsets
        converter = CPM_CPN_Converter(petriNet=self.__petriNet, causalModel=self.__causalModel)
        converter.convert()
