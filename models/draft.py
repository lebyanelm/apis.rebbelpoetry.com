from models.poem import Poem


class Draft(Poem):
	def __init__(self, data):
		super().__init__(data, True)

		self.did = data.get("did")