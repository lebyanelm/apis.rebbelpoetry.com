from mongoengine import Document, StringField, IntField, FloatField, ListField, ObjectIdField


class Report(Document):
	of = ObjectIdField()
	reporter = ObjectIdField()
	reason = StringField()