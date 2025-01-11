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
