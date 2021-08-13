# dependencies
from models.data import Data

class Tag(Data):
	def __init__(self, name, is_automatic=False):
		super().__init__()

		self.name = name
		self.reads = []
		self.reads_count = 0
		self.is_automatic = is_automatic
		self.publishes = []
		self.publishes_count = 0

		_schema_version_ = 1.0
