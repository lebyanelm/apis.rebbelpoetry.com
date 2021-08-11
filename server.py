# dependencies
import os
import mongo_connection
from dotenv import dotenv_values
from flask import Flask, request, send_file
from flask_cors import CORS, cross_origin


# models
import models.response


# controllers
import controllers.accounts as AccountsController
import controllers.upload_resources as UploadsController
import controllers.poems as PoemsController


# helpers
from helpers.authentication import is_authenticated


####### SERVER ENVIRONMENTAL VARIABLES SETUP ##########
config = { **dotenv_values('.env.shared') }

if config['ENVIRONMENT'] == config['DEVELOPMENT_MODE']:
	config = { **config, **dotenv_values('.env.secret') }

os.environ = {
	**os.environ,
	**config
}



###### MAKE A DATABASE CONNECTION ########
mongodb_client = mongo_connection.create_mongodb_connection(os.environ['ENVIRONMENT'])



####### START A SERVER AND API ROUTES ########
server = Flask(__name__, static_folder="./uploads/", static_url_path="/api/uploads/")
CORS(server, resources={ r"*": { "origins": "*" } })



########## ACCOUNT FACILITATION AND USER MANAGEMENT ##########
@server.route("/api/poets", methods=["POST", "PUT"])
@cross_origin()
def create_user_account() -> str:
	return AccountsController.create_user_account()

@server.route("/api/poets", methods=["GET"])
@cross_origin()
def get_listed_poets():
	return AccountsController.get_listed_poets()

@server.route("/api/poets/reauthenticate", methods=["GET"])
@cross_origin()
def reauthenticate_user_session():
	return AccountsController.reauthenticate_user_session()

@server.route("/api/poets/<email_address>", methods=["GET"])
@cross_origin()
def request_user_profile(email_address):
	return AccountsController.request_user_profile(email_address)

@server.route("/api/poets/<email_address>", methods=["PATCH"])
@cross_origin()
def make_account_changes(email_address):
	return AccountsController.make_account_changes(email_address)

@server.route("/api/poets/authentication", methods=["GET"])
@cross_origin()
def request_user_authentication():
	return AccountsController.request_user_authentication()


"""
Upload resources manager.
Handles file uploads and asset preview routes
Also handles avatar/display_photo upload
"""
@server.route("/api/assets/upload", methods=["POST", "PUT"])
@cross_origin()
@is_authenticated
def handle_resource_upload():
	return UploadsController.handle_resource_upload()

@server.route("/api/uploads/<uploaded_resource>", methods=["GET"])
@cross_origin()
def get_upload_resource_urls(uploaded_resource):
	return UploadsController.get_upload_resource_urls(uploaded_resource)


"""
Managing and publishing of poems.
"""
@server.route("/api/poems", methods=["POST", "PUT"])
@cross_origin()
@is_authenticated
def publish_a_poem():
	return PoemsController.publish_a_poem()


######### SET THE SERVER TO RUN #########
IS_DEBUG_MODE = os.environ["ENVIRONMENT"] == os.environ["DEVELOPMENT_MODE"]
server.run(debug=IS_DEBUG_MODE, host="localhost")
