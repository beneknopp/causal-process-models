import xml.etree.ElementTree as ET


class DOM_Element(object):

    attributes: dict
    child_elements: []
    hasText: bool = False
    text: str

    def __init__(self, tag, attributes, child_elements=None):
        if child_elements is None:
            child_elements = []
        self.tag = tag
        self.attributes = attributes
        self.child_elements = child_elements

    def set_text(self, text):
        self.hasText = True
        self.text = text

    def get_text(self):
        return self.text

    def to_DOM_Element(self, parent):
        element = ET.SubElement(parent, self.tag)
        for attribute_key, attribute_value in self.attributes.items():
            element.set(attribute_key, attribute_value)
        if self.hasText:
            element.text = self.text
        for child in self.child_elements:
            child.to_DOM_Element(element)
        return element

    def add_child(self, child):
        self.child_elements.append(child)

    def add_children(self, children):
        self.child_elements = self.child_elements + children

    def get_children_by_tag(self, tag):
        return list(filter(lambda c: tag in c.tag and c.tag in tag, self.child_elements))

    def scale(self, factor):
        scale_posattr = getattr(self, "scale_posattr", None)
        if callable(scale_posattr):
            scale_posattr(factor)
        for child in self.child_elements:
            child.scale(factor)
        for child in self.child_elements:
            child.readjust()

    def readjust(self):
        readjust_pos = getattr(self, "readjust_pos", None)
        if callable(readjust_pos):
            readjust_pos()
        for child in self.child_elements:
            child.readjust()
