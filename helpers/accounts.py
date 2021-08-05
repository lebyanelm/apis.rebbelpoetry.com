# dependencies
import mongoengine
import sys


# -> reading through a database and retrieving a certain user using thier username
# -> returns None if no user was found, and returns False if database connection not found
def get_user(username) -> Account.Account:
    try:
        # -> get the connection instance from the mongoengine and get the database pointer to read from it
        collection = mongoengine.get_connection().get_database(name='at').get_collection('account')
        cursor = collection.find({'username' : username})
        user = None

        for account in cursor:
            user = account
            break

        return user

    except mongoengine.connection.ConnectionFailure as error:
        print('Connection Error', error)
        return False


# -> saves changes made to a certain user account
# -> returns True if user was found and changes were saved, returns False if changes were not made
def save_user_changes(changes) -> bool:
    try:
        # -> get the connection instance from the mongoengine and get the database pointer to read from it
        collection = mongoengine.get_connection().get_database(name='at').get_collection('account')

        # -> remove the object ID from the changes and save them somewhere else
        account_object_id = changes['_id']
        del changes['_id']

        # -> find and update the account details
        collection.find_one_and_update(
            { '_id' : account_object_id },
            { '$set' : changes }
        )

        # set back the object ID as a string
        changes['_id'] = str(account_object_id)

        # -> let the caller know the changes were made
        return True
    except:
        print(sys.exc_info()[0])
        # -> let the caller know an error was discovered
        return False


# -> Takes account data and removes data params that are sensative to the public
def sanitize_account(account: Account, is_allow_preferences = True) -> Account:
    if account.get('password') is not None:
        del account['password']
    if account.get('verification_code') is not None:
        del account['verification_codes']
    if account.get('allowed_messengers') is not None:
        del account['allowed_messengers']
    if account.get('messages') is not None:
        del account['messages']

    if is_allow_preferences == False:
        if account.get('preferences') is not None:
            del account['preferences']

    # return the cleaned up account data
    return account