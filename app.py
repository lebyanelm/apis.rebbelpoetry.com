# dependencies
import os
import bson
import mongo_connection
from dotenv import dotenv_values
from flask import Flask, request, send_file, g
from flask_cors import CORS, cross_origin


# models
from models.response import Response
from models.data import Data
from models.report import Report


# schemas
from schemas.report import Report as _Report


# controllers
import controllers.accounts as AccountsController
import controllers.upload_resources as UploadsController
import controllers.poems as PoemsController
import controllers.comments as CommentsController


# helpers
from helpers.authentication import is_authenticated
from helpers.poems import get_poem_document, update_poem_document
from helpers.database import get_from_collection, update_a_document
from helpers.request import read_request_body, query_string_to_dict


####### SERVER ENVIRONMENTAL VARIABLES SETUP ##########
config = {**dotenv_values('.env.shared')}

if os.environ.get("PRODUCTION_ENVIRONMENT") is None:
    config = {**config, **dotenv_values('.env.secret')}

os.environ = {
    **os.environ,
    **config
}


###### MAKE A DATABASE CONNECTION ########
mongodb_client = mongo_connection.create_mongodb_connection()


####### START A SERVER AND API ROUTES ########
server = Flask(__name__, static_folder="./uploads/",
               static_url_path="/api/uploads/")
CORS(server, resources={r"*": {"origins": "*"}})


########## ACCOUNT FACILITATION AND USER MANAGEMENT ##########
"""CREATING POET ACCOUNTS"""


@server.route("/api/rebbels", methods=["POST", "PUT"])
@cross_origin()
def create_user_account() -> str:
    return AccountsController.create_user_account()


"""""""USER RE-AUTHENTICATION"""""""


@server.route("/api/rebbels/reauthenticate", methods=["GET"])
@cross_origin()
@is_authenticated
def reauthenticate_user_session():
    return AccountsController.reauthenticate_user_session()


"""""""UPDATE A POET PROFILE"""""""


@server.route("/api/rebbels/<email_address>", methods=["PATCH"])
@is_authenticated
@cross_origin()
def make_account_changes(email_address):
    return AccountsController.make_account_changes(email_address)


"""""""AUTHENTICATING A POET"""""""


@server.route("/api/rebbels/authentication", methods=["GET"])
@cross_origin()
def request_user_authentication():
    return AccountsController.request_user_authentication()


"""""""GETTING POET ACCOUNTS"""""""


@server.route("/api/rebbels", methods=["GET"])
@cross_origin()
def get_listed_poets():
    return AccountsController.get_listed_poets()


"""""""GET A POET PROFILE"""""""


@server.route("/api/rebbels/<username>", methods=["GET"])
@cross_origin()
def request_user_profile(username):
    return AccountsController.request_user_profile(username)


"""""""GETTING A POET PUBLISHED POEMS"""""""


@server.route("/api/rebbels/<email_address>/poems", methods=["GET"])
@is_authenticated
@cross_origin()
def get_poet_poems(email_address):
    return AccountsController.get_poet_poems(email_address)


"""""""GET A SUMMARY OF AUTHORS OF A POEM"""""""


@server.route("/api/authors/<author_ids>", methods=["GET"])
@cross_origin()
def get_listed_author(author_ids):
    return AccountsController.get_listed_author(author_ids)


"""""""GETTING A NEWS FEED OF A USER NOT LOGGED IN"""""""


@server.route("/api/poems/feed", methods=["GET"])
@cross_origin()
def unauthenticated_poemsfeed():
    return PoemsController.unauthenticated_poemsfeed()


"""GETTING A RANDOM POEM"""


@server.route("/api/poems/feeling_lucky", methods=["GET"])
@cross_origin()
def feeling_lucky():
    return PoemsController.feeling_lucky()


"""
Upload resources manager.
Handles file uploads and asset preview routes
Also handles avatar/display_photo upload
"""
"""""""UPLOADING RESOURCES"""""""


@server.route("/api/assets/upload", methods=["POST", "PUT"])
@cross_origin()
@is_authenticated
def handle_resource_upload():
    return UploadsController.handle_resource_upload()


"""""""GETTING AN UPLOADED RESOURCE"""""""


@server.route("/api/uploads/<uploaded_resource>", methods=["GET"])
@cross_origin()
def get_upload_resource_urls(uploaded_resource):
    print(uploaded_resource != "default-avatar.png")
    if (uploaded_resource != "default-avatar.png" and uploaded_resource != "default-background.png"):
        return UploadsController.get_upload_resource_urls(uploaded_resource)
    else:
        default_avatar_path = "/".join([os.getcwd(),
                                       "uploads", uploaded_resource])
        return send_file(default_avatar_path)


"""""""PUBLISHING POEMS"""""""


@server.route("/api/publish/<did>", methods=["POST", "PUT"])
@cross_origin()
@is_authenticated
def publish_a_poem(did: str):
    return PoemsController.publish_a_poem(did)


"""""""UPDATING POEMS"""""""


@server.route("/api/poems/<poem_id>", methods=["POST", "PUT", "PATCH"])
@cross_origin()
@is_authenticated
def update_poem_document_request(poem_id: str):
    return PoemsController.edit_a_poem(poem_id)


"""""""DELETING A POEM"""""""


@server.route("/api/poems/<poem_id>", methods=["DELETE"])
@cross_origin()
@is_authenticated
def delete_poem(poem_id):
    return PoemsController.delete_poem(poem_id)


"""""""DRAFTING A POEM"""""""


@server.route("/api/drafts", methods=["POST"])
@cross_origin()
@is_authenticated
def create_a_draft():
    return PoemsController.create_a_draft()


"""""""GETTING A DRAFT"""""""


@server.route("/api/drafts", methods=["GET"])
@cross_origin()
@is_authenticated
def get_drafts():
    return PoemsController.get_drafts()


"""""""GETTING A POEM DRAFT"""""""


@server.route("/api/drafts/<did>", methods=["GET"])
@cross_origin()
@is_authenticated
def get_a_draft(did: str):
    return PoemsController.get_a_draft(did)


"""""""GETTING POEM COMMENTS"""""""


@server.route("/api/poems/<poem_id>/comments", methods=["GET"])
@cross_origin()
def get_poem_comments(poem_id):
    query_params = query_string_to_dict(request.query_string.decode("ascii"))
    return CommentsController.get_poem_comments(poem_id, query_params.get("start"), query_params.get("limit"))


"""""""REACTING TO A POEM"""""""


@server.route("/api/poems/<poem_id>/react", methods=["POST", "PUT"])
@cross_origin()
@is_authenticated
def like_a_poem(poem_id):
    return PoemsController.react_to_poem(poem_id)


"""""""GETTING A POEM"""""""


@server.route("/api/poems/<poem_id>", methods=["GET"])
@cross_origin()
def get_a_poem(poem_id):
    poem = get_poem_document(poem_id)
    if poem:
        # Update the number of views on the poem as it gets requested
        poem["views_count"] = poem["views_count"] + 1
        update_poem_document(poem_changes=poem)

        # Convert the poem to a JSON-able datatype (dict) for response transports
        poem = Data.to_dict(poem)

        if poem.get("author"):
            poem["author"] = str(poem["author"])

        return Response(200, data=poem).to_json()
    else:
        return Response(404, reason="Poem was not found in record.").to_json()


"""""""SEARCHING POEMS"""""""


@server.route("/api/search", methods=["GET"])
@cross_origin()
def search_poem() -> str:
    # read from the query string of the request
    request_query = query_string_to_dict(request.query_string.decode("ascii"))
    keyword = request_query.get("keyword")

    # if it consists of spaces it'll have + in place of those spaces remove the +
    if "+" in keyword:
        chars_to_replace = {"+": " "}
        for key, value in chars_to_replace.items():
            keyword = keyword.replace(key, value)

    return PoemsController.find_poem_from_keyword(keyword)


"""BOOKMARKING POEMS"""


@server.route("/api/poems/bookmark", methods=["POST", "PUT"])
@cross_origin()
@is_authenticated
def bookmark_a_poem():
    return PoemsController.bookmark_a_poem()


"""GETTING POEM TAGS"""
# No authentication required.


@server.route("/api/tags/<tags>", methods=["GET"])
@cross_origin()
def get_poem_tags(tags):
    return PoemsController.get_poem_tags(tags)


# Commentations on Poems
"""""""POSTING COMMENTS ON POEMS"""""""


@server.route("/api/poems/<poem_id>/comments", methods=["POST", "PUT"])
@cross_origin()
@is_authenticated
def post_a_comment(poem_id: str):
    return CommentsController.post_a_comment(poem_id)


"""""""DELETING COMMENTS"""""""


@server.route("/api/poems/comments/<comment_id>", methods=["DELETE"])
@cross_origin()
@is_authenticated
def delete_a_comment(comment_id):
    return CommentsController.delete_a_comment(comment_id)


"""""""REACTING TO A COMMENT"""""""


@server.route("/api/poems/comments/<comment_id>/react", methods=["POST", "PUT"])
@cross_origin()
@is_authenticated
def react_to_comment(comment_id):
    return CommentsController.react_to_comment(comment_id)


"""""""TODO: UPDATE A COMMENT"""""""


@server.route("/api/poems/comments/<comment_id>", methods=["POST", "PUT", "PATCH"])
@cross_origin()
@is_authenticated
def edit_a_comment(comment_id):
    return CommentsController.edit_a_comment(comment_id)


"""""""REPORTING CONTENT"""""""


@server.route("/api/report/<content_type>/<content_id>", methods=["POST", "PUT"])
@cross_origin()
@is_authenticated
def report_content(content_type, content_id):
    request_data = read_request_body(request)
    auth_data = g.my_request_var["payload"]

    reporter = get_from_collection(
        search_value=auth_data["email_address"], search_key="email_address", collection_name="accounts")
    if reporter:
        if content_type == "poems" or content_type == "comments":
            report_data = Report({
                **request_data,
                "reporter": reporter["_id"],
                "content_type": content_type,
                "of": bson.objectid.ObjectId(content_id)})
            report = _Report(
                **{**report_data.__dict__, "_id": bson.objectid.ObjectId()})

            if content_type == "poems":
                content_data = get_poem_document(content_id)
            else:
                content_data = get_from_collection(
                    search_value=content_id, search_key="_id", collection_name="comments")

            content_data["reports"].append(report._id)
            content_data["reports_count"] = len(content_data["reports"])

            # save the report and update the reported content
            report.save()
            update_a_document(document_changes=content_data,
                              collection_name=content_type)

            # prepare the response
            response_data = {**report_data.__dict__, "_id": str(report._id)}
            response_data["of"] = str(response_data["of"])
            response_data["reporter"] = str(response_data["reporter"])

            return Response(200, data=response_data).to_json()
        else:
            return Response(400, reason="Unknown content type to be reported.").to_json()
    else:
        return Response(404, reason="Your account was not found in record.").to_json()


print(os.environ)
######### SET THE SERVER TO RUN #########
IS_DEBUG_MODE = os.environ.get("PRODUCTION_ENVIRONMENT") is None
server.run(debug=IS_DEBUG_MODE, host="localhost")
