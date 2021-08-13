import bson
from models.data import Data


class Comment(Data):
	def __init__(self, data):
		self.of = data.get("of")
		self.body = data.get("body")
		self.commentor = data.get("commentor")
		self.reply_of = data.get("reply_of")
		self.replies = data.get("replies")
		
		self.likes = []
		self.likes_count = 0
		self.dislikes = []
		self.dislikes_count = 0
		self.reports = []
		self.reports_count = 0

		if self.of is not None:
			self.of = bson.objectid.ObjectId(self.of)
		
		if self.reply_of is not None:
			self.reply_of = bson.objectid.ObjectId(self.reply_of)
		
		if self.replies == None:
			self.replies = []