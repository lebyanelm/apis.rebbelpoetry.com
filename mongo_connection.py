# dependencies
import mongoengine
import os
import pymongo as pymongo

# create a connection with mongo according to the current active environment
def create_mongodb_connection(environment) -> pymongo.MongoClient:
    if environment == os.environ['PRODUCTION_MODE']:
        client = pymongo.MongoClient(host=os.environ['PROD_MONGODB'])
    else:
        client = mongoengine.connect(host=os.environ['DEV_MONGODB'])
    return client
