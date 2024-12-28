# IDs that are already used
blocked_ids: set


class CPN_ID_Manager:

    def __init__(self, xmlstring):
        self.ID_counter = 1
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
