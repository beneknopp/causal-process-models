from causal_model import causal_process_model
from causal_model.causal_process_model import CausalProcessModel
from process_model.petri_net import SimplePetriNet
from simulation_model.cpm_cpn_converter import CPM_CPN_Converter
from simulation_model.simulation_parameters import SimulationParameters
from utils.validators import validate_condition


class SimulationModel:

    def __validate(self):
        petri_net_activities = self.__petriNet.get_activities()
        causal_model_activities = self.__causalModel.get_activity_names()
        validate_condition(all(
            act in petri_net_activities
            for act in causal_model_activities))
        activities_with_simulation_parameters = self.__simulationParameters.get_activity_names()
        activities_without_simulation_parameters = [
            activity_name for activity_name in petri_net_activities
            if activity_name not in activities_with_simulation_parameters
        ]
        validate_condition(
            not len(activities_without_simulation_parameters),
            "There are activities {0} with unspecified simulation parameters.".format(
                activities_without_simulation_parameters
            ))

    def __init__(self,
                 petriNet: SimplePetriNet,
                 causalModel: CausalProcessModel,
                 simulation_parameters: SimulationParameters):
        self.__petriNet = petriNet
        self.__causalModel = causalModel
        self.__simulationParameters = simulation_parameters
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
        # create colsets
        cpn_template_path = "resources/empty.cpn"
        cpn_output_path = "output/simulation_model.cpn"
        converter = CPM_CPN_Converter(cpn_template_path,
                                      petriNet=self.__petriNet,
                                      causalModel=self.__causalModel,
                                      simulationParameters= self.__simulationParameters)
        converter.convert()
        converter.export(cpn_output_path)
