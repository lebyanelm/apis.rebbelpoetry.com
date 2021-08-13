import bson
from flask import request, g


# models
from models.comment import Comment
from models.response import Response


# schemas
from schemas.comment import Comment as _Comment


# helpers
from helpers.request import read_request_body
from helpers.poems import get_poem_document, update_poem_document, get_tag_document, update_tag_document
from helpers.database import get_from_collection, update_a_document, delete_documents


"""""""""POSTING COMMENTS"""""""""
def post_a_comment(poem_id: str) -> str:
	request_data = read_request_body(request)
	auth_data = g.my_request_var["payload"]

	commentor = get_from_collection(search_value=auth_data["email_address"], search_key="email_address", collection_name="accounts")
	if commentor:
		request_data["commentor"] = commentor["_id"]
		poem = get_from_collection(search_value=bson.objectid.ObjectId(poem_id), search_key="_id", collection_name="poems")
		if poem:
			request_data["of"] = poem["_id"]
			comment = Comment(request_data)
			comment_schema = _Comment(**{**comment.__dict__, "_id": bson.objectid.ObjectId()})

			comment_schema.save()

			# look if the comment is a reply of another comment
			if comment.reply_of:
				parent_comment = get_from_collection(search_value=comment.reply_of, search_key="_id", collection_name="comments")
				if parent_comment:
					parent_comment["replies"].append(comment_schema._id)
					update_a_document(document_changes=parent_comment, collection_name="comments")

			poem["comments"].append(comment_schema._id)
			poem["comments_count"] = len(poem["comments"])

			is_poem_saved = update_poem_document(poem)
			if is_poem_saved:
				is_commentor_saved = update_a_document(document_changes=commentor)
				if is_commentor_saved:
					# prepare the response for being sent back to the commentor
					response_data = comment.to_dict()

					response_data["_id"] = str(comment_schema._id)
					response_data["of"] = str(response_data["of"])
					if response_data["reply_of"] is not None:
						response_data["reply_of"] = str(response_data["reply_of"])

					response_data["commentor"] = str(response_data["commentor"])

					return Response(200, data=response_data).to_json()
				else:
					return Response(500, reason="Something went wrong while saving your account.").to_json()
			else:
				return Response(500, reason="Something went wrong while saving the poem.").to_json()
		else:
			return Response(404, reason="Poem was not found. It may have been deleted.").to_json()
	else:
		return Response(404, reason="Your account was not found in record.").to_json()

	return Response(200).to_json()


"""""""""REACTING TO COMMENTS"""""""""
def react_to_comment(comment_id: str, reaction: str) -> str:
	auth_data = g.my_request_var["payload"]
	reactor = get_from_collection(search_value=auth_data.get("email_address"), search_key="email_address", collection_name="accounts")
	if reactor:
		comment_id = bson.objectid.ObjectId(comment_id)
		comment = get_from_collection(search_value=comment_id, search_key="_id", collection_name="comments")
		if comment:
			reactor_id = bson.objectid.ObjectId(reactor["_id"])
			# reset the reaction state of the user, if any
			if reactor_id in comment["likes"]:
				comment["likes"].remove(reactor_id)
				comment["likes_count"] = len(comment["likes"])
			elif reactor_id in comment["dislikes"]:
				comment["dislikes"].remove(reactor_id)
				comment["dislikes_count"] = len(comment["dislikes"])

			if reaction == "like":
				comment["likes"].append(reactor_id)
				comment["likes_count"] = len(comment["likes"])
			elif reaction == "dislike":
				comment["dislikes"].append(reactor_id)
				comment["dislikes_count"] = len(comment["dislikes"])

			# update the comment
			is_comment_saved = update_a_document(document_changes=comment, collection_name="comments")
			if is_comment_saved:
				return Response(200).to_json()
			else:
				return Response(500, reason="Something went wrong while saving the comment.").to_json()
		else:
			return Response(404, reason="Comment was not found in record.").to_json()
	else:
		return Response(404, reason="Your account was not found in record.").to_json()


"""""""""DELETING COMMENTS"""""""""
def delete_a_comment(comment_id):
	auth_data = g.my_request_var["payload"]
	account = get_from_collection(search_value=auth_data.get("email_address"), search_key="email_address", collection_name="accounts")

	if account:
		comment_id = bson.objectid.ObjectId(comment_id)
		comment = get_from_collection(search_value=comment_id, search_key="_id", collection_name="comments")
		if comment:
			poem = get_poem_document(comment["of"])
			if poem:
				if comment["_id"] in poem["comments"]:
					poem["comments"].remove(comment["_id"])
					poem["comments_count"] = len(poem["comments"])

				is_comment_deleted = delete_documents(search_value=comment_id, search_key="_id", collection_name="comments")
				if is_comment_deleted:
					# update the poem in the poems
					is_poem_saved = update_poem_document(poem)
					if is_poem_saved:
						return Response(200).to_json()
					else:
						return Response(500, reason="Something went wrong while saving the poem.").to_json()
				else:
					return Response(500, reason="Something went wrong while deleting the comment.").to_json()
			else:
				return Response(404, reason="Poem was not found in record.").to_json()
		else:
			return Response(404, reason="Comment was not found in record.").to_json()


"""""""""EDITING COMMENTS"""""""""
def edit_a_comment(comment_id):
	request_data = read_request_body(request)
	auth_data = g.my_request_var["payload"]
	
	account = get_from_collection(search_value=auth_data["email_address"], search_key="email_address", collection_name="accounts")
	if account:
		comment_id = bson.objectid.ObjectId(comment_id)
		comment = get_from_collection(search_value=comment_id, search_key="_id", collection_name="comments")
		if comment:
			if comment["commentor"] == account["_id"]:
				comment["body"] = request_data["body"]
				is_comment_saved = update_a_document(document_changes=comment, collection_name="comments")
				if is_comment_saved:
					return Response(200).to_json()
				else:
					return Response(500, reason="Something went wrong while saving the comment.").to_json()
			else:
				return Response(403, reason="You are not allowed to edit this comment.").to_json()
		else:
			return Response(404, reason="Your comment was not found in record.")
	else:
		return Response(404, reason="Your account was not found in record.").to_json()