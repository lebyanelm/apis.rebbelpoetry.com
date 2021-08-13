from mongoengine import Document, StringField, IntField, FloatField, ListField, ObjectIdField


class Report(Document):
	_id = ObjectIdField()
	of = ObjectIdField()
	reporter = ObjectIdField()
	reason = StringField()
	description = StringField()

	meta = { "strict": False, "collection": "reports"}