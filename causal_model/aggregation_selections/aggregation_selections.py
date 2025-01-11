from abc import abstractmethod, ABC as AbstractBaseClass

from causal_model.causal_process_structure import AttributeRelation
from simulation_model.colset import get_object_type_colset_name, get_real_colset_name, \
    get_attribute_all_observations_colset_name
from utils.sml_coding import SML_Codeable



class AggregationSelection(SML_Codeable, AbstractBaseClass):

    def __init__(self, name, r: AttributeRelation):
        super().__init__()
        self.__name = name
        self.__r = r
        in_attribute  = r.get_in()
        out_attribute = r.get_out()
        in_type  = in_attribute.get_activity().get_leading_type()
        out_type = out_attribute.get_activity().get_leading_type()
        self.object_type_in  = in_type
        self.object_type_out = out_type
        self.attribute_in = in_attribute
        self.attribute_out = out_attribute
        self.auxiliary_functions: list[SML_Codeable] = self.make_auxiliary_functions()

    def get_function_name(self):
        return self.__name

    def get_relation(self):
        return self.__r

    def get_parameter_string(self):
        """
        Example: (Selecting values from colset C_domain)

        "(x: C_orders, t: TIME, ys)"

        where ys is a list of products (y1: C_items, y2: TIME, y3: C_domain)

        :return: such parameter string
        """
        leading_colset_name = get_object_type_colset_name(self.object_type_out)
        timestamp_colset_name = get_real_colset_name()
        allobs_colset_name = get_attribute_all_observations_colset_name(self.attribute_in.get_id())
        return "x: {0}, t: {1}, ys: {2}".format(leading_colset_name, timestamp_colset_name, allobs_colset_name)

    @abstractmethod
    def to_SML(self):
        pass

    @abstractmethod
    def make_auxiliary_functions(self):
        pass



