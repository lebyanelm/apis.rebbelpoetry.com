import sys
import os
import mongoengine


from models.account import Account


# -> reading through a database and retrieving a certain user using thier username
# -> returns None if no user was found, and returns False if database connection not found
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
        # -> get the connection instance from the mongoengine and get the database pointer to read from it
        collection = mongoengine.get_connection().get_database(name=os.environ["DATABASE_NAME"]).get_collection("accounts")
        cursor = collection.find({ search_key : search_value })
        user = None

        for account in cursor:
            user = account
            break

        return user

    except mongoengine.connection.ConnectionFailure as error:
        print("Connection Error", error)
        return False


# -> saves changes made to a certain user account
# -> returns True if user was found and changes were saved, returns False if changes were not made
def save_user_changes(changes) -> bool:
    try:
        # -> get the connection instance from the mongoengine and get the database pointer to read from it
        collection = mongoengine.get_connection().get_database(name=os.environ["DATABASE_NAME"]).get_collection("accounts")

        # -> remove the object ID from the changes and save them somewhere else
        account_object_id = changes["_id"]
        del changes["_id"]

        # -> find and update the account details
        collection.find_one_and_update(
            { "_id" : account_object_id },
            { "$set" : changes }
        )

        # set back the object ID as a string
        changes["_id"] = str(account_object_id)

        # -> let the caller know the changes were made
        return True
    except:
        print(sys.exc_info()[0])
        # -> let the caller know an error was discovered
        return False