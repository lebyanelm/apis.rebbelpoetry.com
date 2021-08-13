from mongoengine import Document, StringField, IntField, FloatField, ListField, ObjectIdField


class Comment(Document):
	_id = ObjectIdField()
	of = ObjectIdField()
	body = StringField()
	commentor = ObjectIdField()
	reply_of = ObjectIdField()
	replies = ListField(default=[])
	
	likes = ListField(default=[])
	likes_count = IntField(default=0)

	dislikes = ListField(default=[])
	dislikes_count = IntField(default=0)

	reports = ListField(default=[])
	reports_count = IntField(default=0)

	_schema_version_ = FloatField(default=1.0)

	meta = { "strict": False, "collection": "comments" }