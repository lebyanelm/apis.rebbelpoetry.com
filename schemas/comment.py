from mongoengine import Document, StringField, DictField, IntField, FloatField, ListField, ObjectIdField, BooleanField


class Comment(Document):
    _id = ObjectIdField()
    time_created = DictField()
    last_modified = DictField()

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

    is_edited = BooleanField(default=False)

    _schema_version_ = FloatField(default=1.0)

    meta = {"strict": False, "collection": "comments"}
