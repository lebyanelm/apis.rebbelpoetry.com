# dependencies
import os
import sys
import jwt
from datetime import datetime, timedelta
from models.account import Account
from flask import request


# Helpers
from helpers.response_messages import RESPONSE_MESSAGES


"""
Helper functions to handle authentication
"""

# -> Authenticates a request and finds and returns a boolean if authenticated
def is_authenticated(_request: request) -> bool:
    authentication_data = _request.headers.get('Authorization')

    # -> check if any request data has been provided (eg. Bearer <TOKEN>)
    if authentication_data != None:
        # -> get the authentication method provided. Only Bearer method allowed
        authentication_data_split = authentication_data.split(' ')
        authentication_method = authentication_data_split[0]

        if authentication_method == 'Bearer':
            try:
                token = authentication_data_split[1]
                authentication_data_decoded = jwt.decode(token, os.environ['SECRET'],
                    options={ "verify_signature": False, "verify_aud" : False, "verify_exp" : True })
                return 200, authentication_data_decoded
            except:
                error = sys.exc_info()[0]
                if error == jwt.exceptions.ExpiredSignatureError:
                    return 510, RESPONSE_MESSAGES[510]
                else:
                    return 403, RESPONSE_MESSAGES[403]
        else:
            return False, 'Unsupported authentication method.'
    else:
        return False, 'No authentication provided.'


# -> Takes account data and removes data params that are sensative to the public
def sanitize_account(account: Account, is_allow_preferences = True) -> Account:
    if account.get('password') is not None:
        del account['password']
    if account.get('verification_code') is not None:
        del account['verification_codes']

    if is_allow_preferences == False:
        if account.get('preferences') is not None:
            del account['preferences']

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
            "email_address" : email_address,
            "exp" : now + expires
        },
        os.environ['SECRET'],
        algorithm="HS256")
    ])