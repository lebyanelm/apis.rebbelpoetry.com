# dependencies
import readtime
import bson
from models.data import Data
from polyglot.detect import Detector


# models
from models.tag import Tag


# schemas
from schemas.tag import Tag as _Tag


# helpers
from helpers.poems import parse_poem_tags_string, get_tag_document, update_tag_document


class Poem(Data):
	def __init__(self, data, is_draft=False):
		super().__init__()

		self._id = bson.objectid.ObjectId()
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


		if self.languages == None and is_draft == False:
			# automatically detect the languages
			self.languages = self.detect_language()

		# default values
		self.read_time = self.get_read_time().__str__()
		self.bookmarks_count = 0
		self.likes = []
		self.likes_count = 0
		self.dislikes = []
		self.dislikes_count = 0
		self.shares_count = 0
		self.views_count = 0
		self.comments_count = 0
		self.comments = []
		self.reports = []
		self.reports_count = 0


		other_possible_tags = []
		if self.featured_poets:
			other_possible_tags.append("features")
		
		if self.audio_file:
			other_possible_tags.append("audio")
		
		if self.collection:
			other_possible_tags.append("collection")
		
		if self.languages and len(self.languages):
			other_possible_tags.append(self.languages[0]["name"].lower())

		if self.tags == None:
			# automatically come up with tags
			self.tags = other_possible_tags
		self.tags = [self.read_time, *self.tags, *other_possible_tags]
		self.parse_current_tags()

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
		

	def parse_current_tags(self):
		if self.tags and len(self.tags) > 0:
			for index, tag_name in enumerate(self.tags):
				existing_tag = get_tag_document(tag_name)

				if existing_tag == None:
					tag_data = Tag(tag_name)
					existing_tag = _Tag(**{**tag_data.__dict__, "_id": bson.objectid.ObjectId()})
					
				if type(existing_tag) == _Tag:
					if self._id not in existing_tag.publishes:
						existing_tag.publishes.append(self._id)
						existing_tag.publishes_count = len(existing_tag.publishes)
						self.tags[index] = existing_tag._id
						existing_tag.save()
				else:
					if self._id not in existing_tag["publishes"]:
						existing_tag["publishes"].append(self._id)
						existing_tag["publishes_count"] = len(existing_tag["publishes"])
						self.tags[index] = existing_tag["_id"]
						update_tag_document(existing_tag)
