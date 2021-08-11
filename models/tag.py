# dependencies
from models.data import Data

class Tag(Data):
	def __init__(self, name):
		super().__init__()

		self.name = name
		self.reads = []
		self.reads_count = 0
		self.publishes = []
		self.publishes_count = 0
