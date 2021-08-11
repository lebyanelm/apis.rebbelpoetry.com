# dependencies
import readtime
from models.data import Data
from polyglot.detect import Detector


from helpers.poems import parse_poem_tags_string


class Poem(Data):
	def __init__(self, data):
		super().__init__()

		self.thumbnail = data.get("thumbnail")
		self.title = data.get("title")
		self.body = data.get("body")
		self.description = data.get("description")
		self.author = data.get("author")
		self.featured_poets = data.get("featured_poets")
		self.audio_file = data.get("audio_file")
		self.tags = parse_poem_tags_string(data.get("tags"))
		self.collection = data.get("collection")
		self.languages = data.get("language")


		if self.languages == None:
			# automatically detect the languages
			self.languages = self.detect_language()

		# default values
		self.read_time = self.get_read_time().__str__()
		self.commentation = []
		self.edits = []
		self.audio_syncing = {}
		self.bookmarks_count = 0
		self.likes_count = 0
		self.shares_count = 0
		self.views_count = 0
		self.comments_count = 0
		self.comments = []

		other_possible_tags = [self.read_time]
		if self.featured_poets:
			other_possible_tags.append("features")
		
		if self.audio_file:
			other_possible_tags.append("audio")

		if len(self.commentation):
			other_possible_tags.append("commentations")
		
		if self.collection:
			other_possible_tags.append("collection")
		
		if self.languages and len(self.languages):
			other_possible_tags.append(self.languages[0]["name"].lower())

		if self.tags == None:
			# automatically come up with tags
			self.tags = other_possible_tags
		self.tags = [*self.tags, *other_possible_tags]

		self._schema_version_ = 1.0

	def detect_language(self):
		languages = Detector(self.body).languages
		result_languages = list()
		for language in languages:
			result_languages.append({
				"code" : language.locale.getName(),
				"name" : language.locale.getDisplayName() })
		return result_languages

	def get_read_time(self):
		return readtime.of_text(self.body)

	def detect_keywords(self):
		pass
