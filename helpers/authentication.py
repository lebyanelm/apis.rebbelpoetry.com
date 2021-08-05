# dependencies
import jwt

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
                print(authentication_data_split)
                authentication_data_decoded = jwt.decode(authentication_data_split[1], os.environ['SECRET'], algorithms='HS256')
                return True, authentication_data_decoded
            except:
                print(sys.exc_info()[0])
                return False, 'Invalid or expired authentication provided.'
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
    if account.get('allowed_messengers') is not None:
        del account['allowed_messengers']
    if account.get('messages') is not None:
        del account['messages']

    if is_allow_preferences == False:
        if account.get('preferences') is not None:
            del account['preferences']

    # return the cleaned up account data
    return account


# -> Takes in a username and generates a Token for the username
def generate_token(username: str) -> str:
    return jwt.encode(
        { 'username': username }, os.environ['SECRET'], algorithm="HS256")