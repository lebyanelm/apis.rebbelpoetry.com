# dependencies
import datetime


class TimeCreated():
    def __init__(self, timestamp=None):
        date = datetime.datetime.now()

        if timestamp:
            date = datetime.datetime.fromtimestamp(timestamp)

        self.day = date.strftime('%d %A %B, %Y')
        self.time = date.strftime('%I:%M %p')

        if timestamp:
            self.timestamp = timestamp
        else:
            self.timestamp = date.timestamp()
