import os

from pandas import DataFrame

from causal_model.causal_process_model import CausalProcessModel
from object_centric.object_type_structure import ObjectTypeStructure, ObjectType
from object_centric.object_centric_petri_net import ObjectCentricPetriNet as OCPN
from simulation_model.cpm_cpn_converter import CPM_CPN_Converter
from simulation_model.simulation_parameters import SimulationParameters
from utils.validators import validate_condition


class SimulationModel:

    def __validate(self):
        petri_net_activities = self.__petriNet.get_activities()
        causal_model_activities = self.__causalModel.get_activity_names()
        act_not_in_petri_net = [act for act in causal_model_activities if act not in petri_net_activities]
        validate_condition(not len(act_not_in_petri_net),
                           "Activities '{0}' found in causal model, but not in Petri net".format(act_not_in_petri_net))
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
                 petriNet: OCPN,
                 causalModel: CausalProcessModel,
                 objectTypeStructure: ObjectTypeStructure,
                 simulation_parameters: SimulationParameters):
        self.__petriNet = petriNet
        self.__causalModel = causalModel
        self.__objectTypeStructure = objectTypeStructure
        self.__simulationParameters = simulation_parameters
        self.__initial_marking = None
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

    def to_CPN(self, output_path, model_name):
        cwd = os.getcwd()
        output_path_abs = os.path.join(cwd, output_path)
        model_out_path =  os.path.join(output_path_abs, model_name + ".cpn")
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        cpn_template_path = "resources/empty.cpn"
        converter = CPM_CPN_Converter(cpn_template_path,
                                      petriNet=self.__petriNet,
                                      causalModel=self.__causalModel,
                                      simulationParameters=self.__simulationParameters,
                                      objectTypeStructure = self.__objectTypeStructure,
                                      initialMarking = self.__initial_marking,
                                      model_name=model_name)
        converter.convert()
        converter.export(model_out_path)

    def set_initial_marking(self, initial_marking:  dict[ObjectType, DataFrame]):
        self.__initial_marking = initial_marking
