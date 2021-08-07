# Dependencies
import os
import mongoengine
import jwt
import bcrypt
from flask import request
from helpers.request import read_request_body, to_json
from helpers.response_messages import RESPONSE_MESSAGES


# Models
from models.response import Response
from models.account import Account


# Schemas
from schemas.account import Account as _Account


# Helpers
from helpers.accounts import Account, get_user, sanitize_account
from helpers.authentication import generate_token, is_authenticated


"""
Handles account management
and facilitation.
"""


def create_user_account():
	# Read the data sent in the request to verify it
	request_data = read_request_body(request)

	# Make sure the data is sent from the request as expected
	if request_data.get('email_address') and request_data.get('display_name') and request_data.get('password'):
		check_user = get_user(email_address=request_data.get('email_address'))
		if not check_user:
			account_model = Account(request_data)
			# hash the password provided for security purposes
			account_model.password = bcrypt.hashpw(account_model.password.encode('ascii'),
				bcrypt.gensalt()).decode('ascii')

			# after the password was created make a schema object from the model
			account_json = account_model.to_json();
			account_schema = _Account.from_json(account_json)
			account_schema.save()

			# generate a token and a cleaned account data to be used by the user
			authentication_token = generate_token(email_address=account_model.email_address)

			# prepare the response data
			response_data = {
				**sanitize_account(account=account_model.__dict__),
				"token" : authentication_token
			}

			return Response(200, reason=RESPONSE_MESSAGES[200], data=response_data).to_json()
		else:
			return Response(208, reason=RESPONSE_MESSAGES[200]).to_json()
	else:
		return Response(400, reason=RESPONSE_MESSAGES[400]).to_json()


"""
Tokens a generated to expire after a certain period.
When a user requests the latest data, with an expired
token, send back a response to signal a new login or authentication.
"""
def reauthenticate_user_session():
	auth_code, auth_data = is_authenticated(request)
	if auth_code == 200:
		account = get_user(email_address=auth_data.get('email_address'))
		response_data = sanitize_account(account);

		return Response(auth_code, data=response_data).to_json()
	else:
		return Response(auth_code, reason=RESPONSE_MESSAGES[auth_code], message=auth_data).to_json()

	return Response(200).to_json()


"""
Requesting a user account from the database. Usually when showing a preview
of a profile or a whole profile on it's own. Anonymous poems by the user will
be hidden in the public eye. No authentication is required.
"""
def request_user_profile(username):
	user_account_data = get_user(username=username)
	if user_account_data:
		# hide all poems that are published anonymously by this user before sending the data
		for poem in user_account_data['poems']:
			pass
			# check expression here...
		
		# sanitize the account and send back the data
		user_account_data = sanitize_account(user_account_data)

		# send the data back
		return Response(200, data=user_account_data).to_json()
	else:
		return Response(404).to_json()
	return Response(200).to_json()

