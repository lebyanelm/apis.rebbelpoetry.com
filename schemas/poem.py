from mongoengine import Document, IntField, ListField, DictField, StringField, FloatField, ObjectIdField
from bson.objectid import ObjectId


class Poem(Document):
	_id = ObjectIdField()
	time_created = DictField()
	last_modified = DictField()
	
	thumbnail = StringField()
	title = StringField()
	body = StringField()
	description = StringField()
	author = ObjectIdField()

	featured_poets = ListField()
	audio_file = StringField()
	collection = StringField()
	languages = ListField()
	tags = ListField()

	read_time = StringField()
	annotations = ListField()
	edits = ListField()
	audio_syncing = DictField()

	bookmarks_count = IntField()
	likes = ListField()
	likes_count = IntField()
	dislikes = ListField()
	dislikes_count = IntField()
	shares_count = IntField()
	views_count = IntField()
	comments_count = IntField()
	comments = ListField()
	reports = ListField()
	reports_count = IntField()

	_schema_version_ = FloatField()

	meta = { "strict": False, "collection": "poems" }