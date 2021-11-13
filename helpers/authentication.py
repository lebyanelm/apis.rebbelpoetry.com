# dependencies
import os
import sys
import jwt
import traceback
from functools import wraps
from datetime import datetime, timedelta
from models.account import Account
from flask import request, g

# models
from models.response import Response


# Helpers
from helpers.response_messages import RESPONSE_MESSAGES


"""
Helper functions to handle authentication
"""

# authenticates a request and finds and returns a boolean if authenticated


def is_authenticated(fn) -> bool:
    @wraps(fn)
    def decorator_fn(*args, **kwargs):
        authentication_data = request.headers.get('Authorization')
        print("Authentication: ", authentication_data)
        # check if any request data has been provided (eg. Bearer <TOKEN>)
        if authentication_data != None:
            # get the authentication method provided. Only Bearer method allowed
            authentication_data_split = authentication_data.split(' ')
            authentication_method = authentication_data_split[0]

            if authentication_method == 'Bearer':
                try:
                    token = authentication_data_split[1]
                    authentication_data_decoded = decode_authentication_token(
                        token)
                    g.my_request_var = {}
                    g.my_request_var["payload"] = authentication_data_decoded
                    return fn(*args, **kwargs)
                except:
                    error = traceback.format_exc()
                    print(error)
                    if error == jwt.exceptions.ExpiredSignatureError:
                        return Response(510, reason="Authentication expired.").to_json()
                    else:
                        return Response(401, reason="Invalid authentication signature provided.").to_json()
            else:
                return Response(400, reason="Invalid authentication method.").to_json()
        else:
            return Response(400, reason="No authentication provided.").to_json()
    return decorator_fn

# Decodes a base64 token to it's raw data for authentication


def decode_authentication_token(token: str, verify_exp=True) -> dict:
    return jwt.decode(token, os.environ['SECRET'],
                      options={"verify_signature": False, "verify_aud": False, "verify_exp": verify_exp})

# -> Takes account data and removes data params that are sensative to the public


def sanitize_account(account: Account, is_allow_sensitive=True) -> Account:
    if account.get('password') is not None:
        del account['password']
    if account.get('verification_codes') is not None:
        del account['verification_codes']

    if is_allow_sensitive == False:
        if account.get('preferences') is not None:
            del account['preferences']
        if account.get('bookmarked_poems') is not None:
            del account['bookmarked_poems']
        if account.get('archived_poems') is not None:
            del account['archived_poems']
        if account.get('notifications') is not None:
            del account['notifications']
        if account.get('drafts') is not None:
            del account['drafts']
        if account.get('recent_searches') is not None:
            del account['recent_searches']

    # turn object_id into a string for JSON serialization
    if type(account.get('_id')) is not str and account.get('_id') is not None:
        account['_id'] = str(account.get('_id'))

    # return the cleaned up account data
    return account


# -> Takes in a username and generates a Token for the username
def generate_token(email_address: str) -> str:
    token_issuer = os.environ['DEV_API_ENDPOINT']
    if (os.environ['ENVIRONMENT'] == os.environ['PRODUCTION_MODE']):
        token_issuer = os.environ['PROD_API_ENDPOINT']

    now = datetime.utcnow()
    # set the expiry of the token to be 14 days
    expires = timedelta(days=14)

    return ' '.join(['Bearer', jwt.encode(
        {
            "email_address": email_address,
            "exp": now + expires
        },
        os.environ['SECRET'],
        algorithm="HS256")
    ])
