from mongoengine import Document, StringField, ListField, DictField, BooleanField, IntField, FloatField, ObjectIdField
import mongoengine


class Account(Document):
    _id = ObjectIdField(required=False)

    email_address = StringField()
    display_name = StringField()
    username = StringField()
    password = StringField()

    time_created = DictField()
    last_modified = DictField()

    display_photo = StringField()
    poems = ListField()
    featured_poems = ListField()
    archived_poems = ListField()
    bookmarked_poems = ListField()
    drafts = ListField()
    recent_searches = ListField()
    interests = ListField()
    followers = ListField()
    follows = ListField()
    biography = StringField()
    verification_codes = ListField()
    notifications = ListField()
    preferences = DictField()
    previous_usernames = ListField()

    _schema_version_ = FloatField()

    meta = {"strict": False, "collection": "accounts"}
