from abc import ABC as AbstractBaseClass, abstractmethod

from causal_model.causal_process_structure import CPM_Domain, AttributeRelation
from simulation_model.colset import get_domain_colset_name
from utils.sml_coding import SML_Codeable


class AggregationFunction(SML_Codeable, AbstractBaseClass):

    def __init__(self, name, r: AttributeRelation, output_domain: CPM_Domain):
        super().__init__()
        self.__name = name
        self.__r = r
        self.input_domain = r.get_in().get_domain()
        self.input_domain_colset_name = get_domain_colset_name(self.input_domain)
        self.output_domain = output_domain
        self.auxiliary_functions: list[SML_Codeable] = self.make_auxiliary_functions()

    def get_function_name(self):
        return self.__name

    def get_parameter_string(self):
        return "xs: {0} list".format(self.input_domain_colset_name)

    @abstractmethod
    def to_SML(self):
        pass

    @abstractmethod
    def make_auxiliary_functions(self):
        pass
