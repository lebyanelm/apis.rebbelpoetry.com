from mongoengine import Document, IntField, ListField, DictField, StringField, FloatField

class Poem(Document):
	id = StringField(required=False)
	time_created = DictField()
	last_modified = DictField()
	
	thumbnail = StringField()
	title = StringField()
	body = StringField()
	description = StringField()
	author = StringField()

	featured_poets = ListField()
	audio_file = StringField()
	collection = StringField()
	languages = ListField()
	tags = ListField()

	read_time = StringField()
	commentation = ListField()
	edits = ListField()
	audio_syncing = DictField()

	bookmarks_count = IntField()
	likes_count = IntField()
	shares_count = IntField()
	views_count = IntField()
	comments_count = IntField()
	comments = ListField()

	_schema_version_ = FloatField()

	meta = { "strict": False, "collection": "poems" }