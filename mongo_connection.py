# dependencies
import mongoengine
import os
import pymongo as pymongo

# create a connection with mongo according to the current active environment


def create_mongodb_connection() -> pymongo.MongoClient:
    if os.environ.get("PRODUCTION_ENVIRONMENT"):
        client = pymongo.MongoClient(host=os.environ['PRODUCTION_MONGODB'])
        print("MongoDB Connected:", client)
    else:
        client = mongoengine.connect(host=os.environ['DEV_MONGODB'])
        print("MongoDB Connected:", client)
    return client
