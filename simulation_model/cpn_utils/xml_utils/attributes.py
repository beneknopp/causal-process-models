from simulation_model.cpn_utils.xml_utils.dom_element import DOM_Element


class Posattr(DOM_Element):

    __x_default = "0.000000"
    __y_default = "0.000000"

    def __init__(self):
        tag = "posattr"
        attributes = dict()
        attributes["x"] = self.__x_default
        attributes["y"] = self.__y_default
        DOM_Element.__init__(self, tag, attributes)

    def __init__(self, x, y):
        tag = "posattr"
        attributes = dict()
        attributes["x"] = str(x)
        attributes["y"] = str(y)
        DOM_Element.__init__(self, tag, attributes)

    def get_x(self):
        return self.attributes["x"]

    def get_y(self):
        return self.attributes["y"]

    def set_x(self, x):
        self.attributes["x"]  = x

    def set_y(self, y):
        self.attributes["y"] = y

    def scale_posattr(self, factor):
        self.set_x(str(float(self.get_x()) * factor))
        self.set_y(str(float(self.get_y()) * factor))


class Fillattr(DOM_Element):

    __colour_default = "White"
    __filled_default = "false"

    def __init__(self, pattern, colour=__colour_default):
        tag = "fillattr"
        attributes = dict()
        attributes["colour"] = colour
        attributes["pattern"] = pattern
        attributes["filled"] = self.__filled_default
        DOM_Element.__init__(self, tag, attributes)


class Lineattr(DOM_Element):

    __colour_default = "Black"
    __type_default = "Solid"

    def __init__(self, thick, colour: str = __colour_default):
        tag = "lineattr"
        attributes = dict()
        attributes["colour"] = colour
        attributes["thick"] = thick
        attributes["type"] = self.__type_default
        DOM_Element.__init__(self, tag, attributes)


class Textattr(DOM_Element):

    __colour_default = "Black"
    __bold_default = "false"

    def __init__(self, colour: str = __colour_default):
        tag = "textattr"
        attributes = dict()
        attributes["colour"] = colour
        attributes["bold"] = self.__bold_default
        DOM_Element.__init__(self, tag, attributes)


class Arrowattr(DOM_Element):

    __headsize_default = "1.200000"
    __currentcyckle_default = "2"

    def __init__(self):
        tag = "arrowattr"
        attributes = dict()
        attributes["headsize"] = self.__headsize_default
        attributes["currentcyckle"] = self.__currentcyckle_default
        DOM_Element.__init__(self, tag, attributes)