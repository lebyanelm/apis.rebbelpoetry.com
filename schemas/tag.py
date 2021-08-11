from mongoengine import Document, StringField, ListField, DictField, BooleanField, IntField
import mongoengine

class Tag(Document):
	time_created = DictField()
	last_modified = DictField()
	name = StringField()
	reads = ListField(default=[])
	reads_count = IntField(default=0)
	publishes = ListField(default=[])
	publishes_count = IntField(default=0)

	meta = {"strict": False, "collection": "tags"}