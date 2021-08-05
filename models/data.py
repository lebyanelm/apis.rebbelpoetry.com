# dependencies
import nanoid
import models.time_created as TimeCreated


class Data:
    def __init__(self):
        self._id = nanoid.generate(size=30)
        self.time_created = TimeCreated.TimeCreated().__dict__
