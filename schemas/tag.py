from mongoengine import Document, StringField, ListField, DictField, BooleanField, IntField, FloatField, ObjectIdField
import mongoengine

class Tag(Document):
	_id = ObjectIdField()
	time_created = DictField()
	last_modified = DictField()
	name = StringField()
	reads = ListField(default=[])
	is_automatic = BooleanField(default=False)
	reads_count = IntField(default=0)
	publishes = ListField(default=[])
	publishes_count = IntField(default=0)

	_schema_version_ = FloatField()

	meta = {"strict": False, "collection": "tags"}