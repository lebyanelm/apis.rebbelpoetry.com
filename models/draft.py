from models.poem import Poem


class Draft(Poem):
    def __init__(self, data):
        super().__init__(data, True)

        self.owner = data.get("owner")
        self.did = data.get("did")
