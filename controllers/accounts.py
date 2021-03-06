# Dependencies
import os
import re
import bson
import mongoengine
import jwt
import bcrypt
import base64
from flask import request, g


from helpers.request import read_request_body, to_json, query_string_to_dict
from helpers.response_messages import RESPONSE_MESSAGES
from helpers.database import get_from_collection, update_a_document


# Models
from models.response import Response
from models.account import Account


# Schemas
from schemas.account import Account as _Account


# Helpers
from helpers.accounts import Account, get_user, save_user_changes
from helpers.authentication import generate_token, sanitize_account


"""
Handles account management
and facilitation.
"""


def create_user_account():
    # Read the data sent in the request to verify it
    request_data = read_request_body(request)

    # check if theres any data sent in the request
    if request_data:
        # Make sure the data is sent from the request as expected
        if request_data.get('email_address') and request_data.get('display_name') and request_data.get('password'):
            check_user = get_user(
                email_address=request_data.get('email_address'))
            if not check_user:
                account_model = Account(request_data)
                # hash the password provided for security purposes
                account_model.password = bcrypt.hashpw(account_model.password.encode('ascii'),
                                                       bcrypt.gensalt()).decode('ascii')

                # after the password was created make a schema object from the model
                account_schema = _Account(**account_model.__dict__)
                account_schema.save()

                # generate a token and a cleaned account data to be used by the user
                authentication_token = generate_token(
                    email_address=account_model.email_address)

                # prepare the response data
                response_data = {
                    **sanitize_account(account=account_model.to_dict()),
                    "token": authentication_token
                }

                return Response(200, reason=RESPONSE_MESSAGES[200], data=response_data).to_json()
            else:
                return Response(208, reason=RESPONSE_MESSAGES[200]).to_json()
        else:
            return Response(400, reason=RESPONSE_MESSAGES[400]).to_json()
    else:
        return Response(400, reason="Error. Received empty request.").to_json()


"""
Retrieves a list of poets from the backend.
Requires a body limit parameter which has a
default value of 10, and startCount defaulting
to 0 (zero) which is the start of the count.
"""


def get_listed_poets():
    request_query_params = query_string_to_dict(
        request.query_string.decode("ascii"))
    # get the body_count and start_count
    if request_query_params.get("limit"):
        body_limit = int(request_query_params["limit"])
    else:
        body_limit = 10

    if request_query_params.get("start"):
        if request_query_params["start"] == "undefined":
            request_query_params["start"] = 1
        start_count = int(request_query_params["start"]) - 1
        if start_count != 0:
            start_count = start_count * body_limit
    else:
        start_count = 0

    end_count = start_count + body_limit
    print(start_count, end_count)

    # get a cursor from MongoDB database
    try:
        # -> get the connection instance from the mongoengine and get the database pointer to read from it
        collection = mongoengine.get_connection().get_database(
            name=os.environ["DATABASE_NAME"]).get_collection('accounts')
        poets_cursor = collection.find()
        results = []

        # Count how many total results can be retrieved
        total_count = poets_cursor.count()

        for poet in poets_cursor[start_count:end_count]:
            result = sanitize_account(poet, is_allow_sensitive=False)
            # Remove the ObjectIds attached in the document
            result = Account.to_dict(result)

            results.append(result)

        pages_left = int(total_count / body_limit)

        return Response(200, data={"rebbels": results, "total_count": pages_left}).to_json()

    except mongoengine.connection.ConnectionFailure as error:
        print('Connection Error', error)
        return False


"""
Returns a list of author details.
This list will be determined by the IDs
parsed in as an argument
"""


def get_listed_author(author_ids) -> str:
    author_ids = author_ids.rsplit(",")
    documents = list()

    for index, author_id in enumerate(author_ids):
        if author_id != "Anonymous":
            author_ids[index] = bson.objectid.ObjectId(author_id)
            document = get_from_collection(
                search_key="_id", search_value=author_ids[index], collection_name="accounts")
            if document:
                author_ids[index] = bson.objectid.ObjectId(author_ids[index])
                documents.append({
                    "_id": str(document["_id"]),
                    "display_name": document["display_name"],
                    "display_photo": document["display_photo"],
                    "follows": len(document["follows"]),
                    "followers": len(document["followers"]),
                    "poems": len(document["poems"]),
                    "username": document["username"],
                    "biography": document["biography"]})
        else:
            author_ids[index] = "anonymous"
            documents.append({
                "_id": "anonymous",
                "display_name": "Anonymous",
                "display_photo": "",
                "follows": 0,
                "followers": 0,
                "poems": 0,
                "username": "anonymous",
                "biography": "I'm not to be known, I publish my poems under the hood to keep my identity hidden."})

    print(documents)
    return Response(200, data=documents).to_json()


"""
Tokens a generated to expire after a certain period.
When a user requests the latest data, with an expired
token, send back a response to let them know their token
has expired. If token is not yet expired, generate a new one
"""


def reauthenticate_user_session():
    auth_data = g.my_request_var["payload"]
    account = get_user(email_address=auth_data.get("email_address"))
    if account:
        new_token = generate_token(email_address=account["email_address"])
        response_data = {
            **sanitize_account(account),
            "token": new_token
        }
        return Response(200, data=Account.to_dict(response_data)).to_json()
    else:
        return Response(404).to_json()

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
            # TODO: anonymous poems check expression here...

        # sanitize the account and send back the data
        user_account_data = sanitize_account(
            user_account_data, is_allow_sensitive=False)

        # send the data back
        user_account_data = Account.to_dict(user_account_data)
        return Response(200, data=user_account_data).to_json()
    else:
        return Response(404).to_json()
    return Response(200).to_json()


"""
When a user signs in to their account. If authentication is valid,
generate a token and send it back for further easy authentication.
"""


def request_user_authentication():
    try:
        authorization_data = request.headers.get("Authorization")
        if authorization_data and authorization_data != "Basic Og==":
            authorization_data_split = authorization_data.split(' ')
            authorization_method = authorization_data_split[0]
            authorization_data = authorization_data_split[1]
            if authorization_method == "Basic":
                # decode the authentication data
                authorization_data = base64.b64decode(
                    authorization_data).decode("ascii").split(':')
                authorization_username = authorization_data[0]
                authorization_password = authorization_data[1]

                # check if username is an email address or just a username
                email_address_regex = r"^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$"
                is_username_email_address = re.search(
                    email_address_regex, authorization_username)

                # find the user acccount using either the username or email address
                if is_username_email_address:
                    user_account = get_user(
                        email_address=authorization_username)
                else:
                    user_account = get_user(username=authorization_username)

                if user_account:
                    # verify the password given by the request
                    is_password_valid = bcrypt.checkpw(
                        bytes(authorization_password, encoding="utf-8"), bytes(user_account["password"], encoding="utf-8"))
                    if is_password_valid:
                        authentication_token = generate_token(
                            email_address=user_account["email_address"])
                        user_account = sanitize_account(user_account)
                        user_account = Account.to_dict(user_account)
                        return Response(200, data={**user_account, "token": authentication_token}).to_json()
                    else:
                        return Response(403, reason="Password or username incorrect, please check for typing mistakes.").to_json()
                else:
                    return Response(404, reason="Account with that username / email address was not found.").to_json()
            else:
                return Response(501, reason=RESPONSE_MESSAGES[501]).to_json()
        else:
            return Response(403, reason="Request incomplete. No authentication data received.").to_json()
    except:
        return Response(500, reason=RESPONSE_MESSAGES[500]).to_json()


"""
Makes changes to an account.
Only replaces existing parameters, and parts that are strings/numbers/boolean.
Password field can not be changed here.
"""


def make_account_changes(email_address: str) -> str:
    request_data = read_request_body(request)
    auth_data = g.my_request_var["payload"]

    try:
        if request_data:
            user_account = get_user(email_address)
            print(user_account, email_address)
            # make sure the signature of the authentication of from the user
            if user_account:
                if user_account["email_address"] == auth_data.get("email_address"):
                    # loop through every change request data item
                    for parameter in request_data:
                        disallowed_parameters = ["password",
                                                 "_schema_version_", "display_photo", "_id"]
                        # only make an update if the same parameter already exists in account
                        if parameter not in disallowed_parameters:
                            if user_account.get(parameter) is not None:
                                # only make changes to certain data types
                                allowed_data_types = [str, int, bool]
                                if type(request_data[parameter]) in allowed_data_types:
                                    user_account[parameter] = request_data[parameter]
                    # save the changes to the database
                    is_saved = save_user_changes(changes=user_account)
                    if is_saved:
                        # send back the new data
                        response_data = sanitize_account(user_account)
                        return Response(200, data=response_data).to_json()
                    else:
                        return Response(500, reason=RESPONSE_MESSAGES[500]).to_json()
                else:
                    return Response(403, reason=RESPONSE_MESSAGES[403]).to_json()
            else:
                return Response(404, reason="Account is not found in record.").to_json()
        else:
            return Response(400, reason="Error. Received empty request.").to_json()
    except:
        return Response(500).to_json()


def get_poet_poems(poet_id):
    poet = get_user(email_address=poet_id)
    if poet:
        poems = get_from_collection(
            search_value=poet["_id"], search_key="author", collection_name="poems", return_all=True)
        # find and remove anonymous poems
        for index, poem in enumerate(poems):
            if poem.get("is_anonymous") == True:
                poems.remove(poem)
            else:
                poems[index] = Account.to_dict(poem)
                poems[index]["author"] = str(poems[index]["author"])

        return Response(200, data=poems).to_json()
    else:
        return Response(404, reason="Account was not found in record.").to_json()

    return Response(200).to_json()
