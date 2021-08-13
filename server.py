# dependencies
import os
import bson
import mongo_connection
from dotenv import dotenv_values
from flask import Flask, request, send_file, g
from flask_cors import CORS, cross_origin


# models
from models.response import Response
from models.report import Report


# schemas
from schemas.report import Report as _Report


# controllers
import controllers.accounts as AccountsController
import controllers.upload_resources as UploadsController
import controllers.poems as PoemsController


# helpers
from helpers.authentication import is_authenticated
from helpers.poems import get_poem_document, update_poem_document
from helpers.database import get_from_collection, update_a_document
from helpers.request import read_request_body


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
@is_authenticated
def reauthenticate_user_session():
	return AccountsController.reauthenticate_user_session()

@server.route("/api/poets/<email_address>", methods=["GET"])
@cross_origin()
def request_user_profile(email_address):
	return AccountsController.request_user_profile(email_address)

@server.route("/api/poets/<email_address>", methods=["PATCH"])
@is_authenticated
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
@server.route("/api/publish", methods=["POST", "PUT"])
@cross_origin()
@is_authenticated
def publish_a_poem():
	return PoemsController.publish_a_poem()


@server.route("/api/poems/<poem_id>", methods=["POST", "PUT", "PATCH"])
@cross_origin()
@is_authenticated
def update_poem_document(poem_id: str):
	return PoemsController.edit_a_poem(poem_id)


# Commentations on Poems
@server.route("/api/poems/<poem_id>/comments", methods=["POST", "PUT"])
@cross_origin()
@is_authenticated
def post_a_comment(poem_id: str):
	return PoemsController.post_a_comment(poem_id)


# Reacting to a poem
@server.route("/api/poems/<poem_id>/react/<reaction>", methods=["POST", "PUT"])
@cross_origin()
@is_authenticated
def like_a_poem(poem_id, reaction):
	return PoemsController.react_to_poem(poem_id, reaction)

# Reacting to comment of a poem
@server.route("/api/poems/comments/<comment_id>/react/<reaction>", methods=["POST", "PUT"])
@cross_origin()
@is_authenticated
def react_to_comment(comment_id, reaction):
	return PoemsController.react_to_comment(comment_id, reaction)


# Reporting poems and comments: For racism / being disrespectful, etc.
@server.route("/api/report/<content_type>/<content_id>", methods=["POST", "PUT"])
@cross_origin()
@is_authenticated
def report_content(content_type, content_id):
	request_data = read_request_body(request)
	auth_data = g.my_request_var["payload"]

	reporter = get_from_collection(search_value=auth_data["email_address"], search_key="email_address", collection_name="accounts")
	if reporter:
		if content_type == "poems" or content_type == "comments":
			report_data = Report({
				**request_data,
				"reporter": reporter["_id"],
				"content_type": content_type,
				"of": bson.objectid.ObjectId(content_id) })
			report = _Report(**{**report_data.__dict__, "_id": bson.objectid.ObjectId()})
				
			if content_type == "poems":
				content_data = get_poem_document(content_id)
			else:
				content_data = get_from_collection(search_value=content_id, search_key="_id", collection_name="comments")

			content_data["reports"].append(report._id)
			content_data["reports_count"] = len(content_data["reports"])

			# save the report and update the reported content
			report.save()
			update_a_document(document_changes=content_data, collection_name=content_type)

			# prepare the response
			response_data = { **report_data.__dict__, "_id": str(report._id) }
			response_data["of"] = str(response_data["of"])
			response_data["reporter"] = str(response_data["reporter"])
			
			return Response(200, data=response_data).to_json()
		else:
			return Response(400, reason="Unknown content type to be reported.").to_json()
	else:
		return Response(404, reason="Your account was not found in record.").to_json()


######### SET THE SERVER TO RUN #########
IS_DEBUG_MODE = os.environ["ENVIRONMENT"] == os.environ["DEVELOPMENT_MODE"]
server.run(debug=IS_DEBUG_MODE, host="localhost")
