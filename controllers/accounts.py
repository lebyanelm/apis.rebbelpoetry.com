# Dependencies
import os
import mongoengine
import bcrypt
from flask import request
from helpers.request import read_request_body, to_json
from helpers.response_messages import RESPONSE_MESSAGES


# Models
from models.response import Response
from models.account import Account

# Schemas
from schemas.account import Account as _Account

"""
Handles account management
and facilitation.
"""

# Creating an account


def create_user_account():
	# Read the data sent in the request to verify it
	request_data = read_request_body(request)

	# Make sure the data is sent from the request as expected
	if request_data.get('email_address') and request_data.get('display_name') and request_data.get('password'):
		account_model = Account(request_data)
		# hash the password provided for security purposes
		account_model.password = bcrypt.hashpw(account_model.password.encode('ascii'), bcrypt.gensalt()).decode('ascii')

		# after the password was created make a schema object from the model
		account_json = account_model.to_json();
		print(account_json)
		account_schema = _Account.from_json(account_json)
		account_schema.save()

		return Response(200, reason=RESPONSE_MESSAGES['BAD_REQUEST']).to_json()
	else:
		return Response(400, reason=RESPONSE_MESSAGES['BAD_REQUEST']).to_json()
