from abc import abstractmethod, ABC as AbstractBaseClass


class SML_Codeable(AbstractBaseClass):

    def __init__(self):
        pass

    @abstractmethod
    def get_function_name(self):
        pass

    @abstractmethod
    def to_SML(self):
        pass

    def get_call(self):
        function_name = self.get_function_name()
        return lambda parameters: "{0}({1})".format(
            function_name,
            ",".join(parameters)
        )


class AuxiliaryFunction(SML_Codeable):

    def __init__(self, function_name, sml_code):
        super().__init__()
        self.function_name = function_name
        self.sml_code = sml_code

    def get_function_name(self):
        return self.function_name

    def to_SML(self):
        return self.sml_code
