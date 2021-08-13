import sys
import os
import mongoengine


from models.account import Account


# helpers
from helpers.database import get_from_collection, update_a_document


def get_user(email_address = None, username = None, id = None) -> Account:
    search_value = None
    search_key = None
    if email_address:
        search_value = email_address
        search_key = "email_address"
    elif username:
        search_value = username
        search_key = "username"
    else:
        search_value = id
        search_key = "id"
    
    try:
        return get_from_collection(search_value=search_value, search_key=search_key, collection_name="accounts")
    except mongoengine.connection.ConnectionFailure as error:
        print("Connection Error", error)
        return False


def save_user_changes(changes) -> bool:
    try:
        return update_a_document(document_changes=changes, collection_name="accounts")
    except:
        error = sys.exc_info()
        print(error[0], error[1], error[2])

        # -> let the caller know an error was discovered
        return False