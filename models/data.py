# dependencies
import nanoid
import models.time_created as TimeCreated
import bson
import json


class Data:
    def __init__(self):
        self.id = bson.objectid.ObjectId()
        self.time_created = TimeCreated.TimeCreated().__dict__
        self.last_modified = TimeCreated.TimeCreated().__dict__

    def to_json(self) -> str:
        self.id = str(self.id)
        return json.dumps(obj=self.__dict__)