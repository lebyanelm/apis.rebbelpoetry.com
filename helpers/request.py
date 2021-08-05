# dependencies
from flask import request
import json


def read_request_body(request) -> dict:
    # -> reads the binary data sent in the request
    request_data = request.get_data()
    if request_data != b'' or request_data.isascii():
        request_body = request.get_json()
        if request_body != None:
            return request_body
        else:
            False
    else:
        return False


def query_string_to_dict(query_string: str) -> str:
    if '=' in query_string or '&' in query_string:
        result = dict()
        # -> some=query&other=query => ['some=query', 'other=query']
        query_string_items = query_string.split('&')

        # -> loop through the split queries
        for query_item in query_string_items:
            query_item_split = query_item.split('=')
            if len(query_item_split) > 1:
                result[query_item_split[0]] = query_item_split[1]
            else:
                result[query_item_split[0]] = None

        return result
    else:
        return dict()


def to_json(object: dict) -> str:
    convertable_types = [dict, list]
    print(type(object))
    if type(object) not in convertable_types:
        object = object.__dict__
    print(object)
    return json.dumps(object)
