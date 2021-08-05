# DEPENDENCIES
import json
from flask import make_response
import models.http_codes as http_codes


class Response():
    def __init__(self, code: int, reason = None, data = None, message = None):
        try:
            # parse the code to a proper type
            self.status_code = str(code)

            if message != None:
                self.status_message = message
            else:
                 # propely format the response message
                self.status_message = ' '.join(http_codes.HTTP_CODES[code][0].capitalize().split('_'))

            if reason != None:
                self.reason = reason
            
            if data != None:
                self.data = data

        except KeyError as error:
            print('Invalid status code')

    def to_json(self):
        response = make_response(json.dumps(self.__dict__), int(self.status_code))
        response.headers['Content-Type'] = 'application/json'
        return response