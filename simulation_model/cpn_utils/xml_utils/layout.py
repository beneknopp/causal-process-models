from simulation_model.cpn_utils.xml_utils.dom_element import DOM_Element


class Ellipse(DOM_Element):

    __w_default = "60.000000"
    __h_default = "40.000000"

    def __init__(self):
        tag = "ellipse"
        attributes = dict()
        attributes["w"] = self.__w_default
        attributes["h"] = self.__h_default
        DOM_Element.__init__(self, tag, attributes)


class Box(DOM_Element):

    __w_default = "60.000000"
    __h_default = "40.000000"

    def __init__(self, transition_name=None):
        tag = "box"
        attributes = dict()
        attributes["w"] = self.__w_default
        attributes["h"] = self.__h_default
        if transition_name is not None:
            w = str(round(len(transition_name)*7.7 + 5,6))
            attributes["w"] = w
        if transition_name[0] == "t":
            try:
                int(transition_name[1:])
            except ValueError:
                pass
            attributes["w"] = "32.000000"
            attributes["h"] = "26.000000"

        DOM_Element.__init__(self, tag, attributes)


class Snap(DOM_Element):

    __snap_id_default = "0"
    __anchor_horizontal_default = "0"
    __anchor_vertical_default = "0"

    def __init__(self):
        tag = "snap"
        attributes = dict()
        attributes["anchor.horizontal"] = self.__anchor_horizontal_default
        attributes["anchor.vertical"] = self.__anchor_vertical_default
        attributes["snap_id"] = self.__snap_id_default
        DOM_Element.__init__(self, tag, attributes)


class Text(DOM_Element):

    __tool_default = "CPN Tools"
    __version_default = "4.0.1"

    def __init__(self, text=None):
        tag = "text"
        attributes = dict()
        attributes["tool"] = self.__tool_default
        attributes["version"] = self.__version_default
        DOM_Element.__init__(self, tag, attributes)
        if not (text is None):
            self.set_text(text)


class Layout(DOM_Element):

    __tool_default = "CPN Tools"
    __version_default = "4.0.1"

    def __init__(self, text=None):
        tag = "text"
        attributes = dict()
        attributes["tool"] = self.__tool_default
        attributes["version"] = self.__version_default
        DOM_Element.__init__(self, tag, attributes)
        if not (text is None):
            self.set_text(text)
