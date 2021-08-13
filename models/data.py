# dependencies
import nanoid
import models.time_created as TimeCreated
import bson
import json


class Data:
    def __init__(self):
        self.time_created = TimeCreated.TimeCreated().__dict__
        self.last_modified = TimeCreated.TimeCreated().__dict__

    def to_json(self) -> str:            
        return json.dumps(obj=self.__dict__)

    def to_dict(self) -> dict:
        new_self_dict = {**self.__dict__}

        if new_self_dict.get("_id"):
            new_self_dict["_id"] = str(new_self_dict["_id"])
        
        for parameter in new_self_dict:
            if type(new_self_dict[parameter]) == list:
                for index, item in enumerate(new_self_dict[parameter]):
                    new_self_dict[parameter][index] = str(item)

        return new_self_dict