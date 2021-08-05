# dependencies
from mongoengine import Document, StringField, ListField, DictField, BooleanField
import mongoengine


class Account(Document):
    # data items that are required when creating an account
    email_address = StringField()
    display_name = StringField()
    password = StringField()

    # data items that can be given default values
    _id = StringField()
    time_created = DictField()
    display_photo = StringField()
    poems = ListField()
    archived_poems = ListField()
    bookmarked_poems = ListField()
    drafts = ListField()
    recent_searches = ListField()
    followers = ListField()
    follows = ListField()
    biography = StringField(default="")
    verification_codes = ListField()
    notifications = ListField()
