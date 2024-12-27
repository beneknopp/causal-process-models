class CPN(object):

    # colset to set of strings (var identifiers)
    colset_vars_map: dict
    # give variables names like "id1, id2, o1,o2,o3,..." and ensure uniqueness
    var_name_roots = ["id"]
    place_names: set
    # variate node distances in visualization
    coordinate_scaling_factor: float
    places: dict
    transitions: dict
    arcs: dict
    # IDs that are already used
    blocked_ids: set

    def __init__(self, xmlstring, coordinate_scaling_factor=1.0):
        self.ID_counter = 1
        self.colset_vars_map = dict()
        self.place_names = set()
        self.coordinate_scaling_factor = coordinate_scaling_factor
        self.block_ids(xmlstring)

    # determine which ids are already used in template CPN
    def block_ids(self, xmlstr):
        self.blocked_ids = set()
        while xmlstr.find("id=") > 0:
            index = xmlstr.index("id=") + 4
            blocked_id = ""
            char = ""
            while char != '"':
                char = xmlstr[index]
                blocked_id += char
                index = index + 1
            blocked_id = blocked_id[:-1]
            xmlstr = xmlstr[index:]
            self.blocked_ids.add(blocked_id)

    def give_ID(self):
        # in raw cpn file (resources/empty.cpn), ID 0...* are assigned
        # assign 'customized' IDs (IDC)
        ID: str = "ID" + str(self.ID_counter)
        self.ID_counter += 1
        if ID in self.blocked_ids:
            return self.give_ID()
        self.blocked_ids.add(ID)
        return ID

    def add_net_nodes(self, places, transitions, arcs):
        self.places = places
        self.transitions = transitions
        self.arcs = arcs

    def give_colset_place_name(self, colset_name):
        # assign a unique name to a place
        id_root = "".join(list(map(lambda l: l[0].lower(), colset_name.split("_"))))
        count = 1
        while id_root + str(count) in self.place_names:
            count = count + 1
        place_name = id_root + str(count)
        self.place_names.add(place_name)
        return place_name

    def get_one_var(self, colset_name):
        colset_vars = list(set(self.colset_vars_map[colset_name]))
        colset_vars.sort()
        return colset_vars[0]

    def get_some_vars(self, colset_name, number):
        colset_vars = list(set(self.colset_vars_map[colset_name]))
        colset_vars.sort()
        return colset_vars[:number]

    def get_colset_vars_map(self):
        return self.colset_vars_map