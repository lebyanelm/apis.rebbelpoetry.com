# dependencies
import nanoid
import models.time_created as TimeCreated
import bson


class Data:
    def __init__(self):
        self.id = bson.objectid.ObjectId()
        self.time_created = TimeCreated.TimeCreated().__dict__