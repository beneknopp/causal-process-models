class Function(object):

    name: str
    # parameter_name -> colset
    parameters: dict
    declaration: str

    def __init__(self, name, declaration: str = None):
        self.name = name
        self.declaration = declaration