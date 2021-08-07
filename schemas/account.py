# dependencies
from mongoengine import Document, StringField, ListField, DictField, BooleanField, IntField
import mongoengine

class Account(Document):
    # data items that are required when creating an account
    email_address = StringField(unique=True)
    display_name = StringField()
    username = StringField()
    password = StringField()

    # data items that can be given default values
    id = StringField(required=False)
    time_created = DictField()
    display_photo = StringField()
    poems = ListField()
    archived_poems = ListField()
    bookmarked_poems = ListField()
    drafts = ListField()
    recent_searches = ListField()
    followers = ListField()
    follows = ListField()
    biography = StringField()
    verification_codes = ListField()
    notifications = ListField()
    preferences = DictField()
    previous_usernames = ListField()

    meta = {'strict': False}