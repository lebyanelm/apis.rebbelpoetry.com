# dependencies
import os
import sys
import mongoengine
import readtime
import bson
from flask import request, g


# models
from models.poem import Poem
from models.response import Response
from models.tag import Tag
from models.comment import Comment


# helpers
from helpers.request import read_request_body
from helpers.poems import get_poem_document, update_poem_document, get_tag_document, update_tag_document
from helpers.database import get_from_collection, update_a_document


# schema
from schemas.tag import Tag as _Tag
from schemas.account import Account as _Account
from schemas.poem import Poem as _Poem
from schemas.comment import Comment as _Comment


def publish_a_poem():
	request_data = read_request_body(request)
	if request_data:
		poem_data = Poem(request_data)
		poem = _Poem(**poem_data.__dict__)
		featured_poets_not_found = []

		# parse the featured poets and author and turn them into IDs
		author = get_from_collection(search_value=poem.author, search_key="email_address", collection_name="accounts")
		if author:
			poem.author = author["_id"]
			author["poems"].append(poem._id)
			# also parse the featured poets
			for index, featured_poet in enumerate(poem.featured_poets):
				featured_poet = get_from_collection(search_value=bson.objectid.ObjectId(featured_poet), search_key="_id", collection_name="accounts")
				if featured_poet:
					poem.featured_poets[index] = featured_poet["_id"]
					featured_poet["featured_poems"].append(poem._id)
					update_a_document(document_changes=featured_poet, collection_name="accounts")
				else:
					featured_poets_not_found.append(featured_poet_email)
			# save the poem and author account in the database and return it to the user
			poem.save()
			update_a_document(document_changes=author, collection_name="accounts")

			return Response(200, data=poem_data.to_dict()).to_json()
		else:
			return Response(404, reason="Author does not exist.").to_json()
	else:
		return Response(400, reason="Incomplete or missing data.").to_json()


def edit_a_poem(poem_id: str):
	replacement_data = read_request_body(request)
	poem_document = get_poem_document(poem_id)

	# updatable poem attributes
	# -> title
	# -> body
	# -> annotations
	# -> description
	# -> featured poets
	# -> thumbnail
	# -> languages
	# -> collection
	# -> tags

	updatable_attributes = ("title", "body", "annotations", "description", "featured_poets", "thumbnail",
							"languages", "collection", "tags")
	string_attributes = ("title", "body", "description", "thumbnail", "collection", "languages")
	
	for attribute in replacement_data:
		if attribute in updatable_attributes:
			if attribute in string_attributes:
				poem_document[attribute] = replacement_data[attribute]
				# TODO: Be sure to handle a situation where annotations are affected by the body change
				# For the body change also re-calculate the read time
				if attribute == "body":
					poem_document[attribute] = replacement_data[attribute]
					poem_document["read_time"] = readtime.of_text(poem_document[attribute]).__str__()
			else:
				if attribute == "featured_poets":
					poem_document[attribute] = []
					for index, featured_poet in enumerate(replacement_data[attribute]):
						poem_document[attribute].append(bson.objectid.ObjectId(poem_document[attribute][index]))

				elif attribute == "tags":
					poem_document[attribute] = []
					for tag in replacement_data[attribute]:
						existing_tag = get_tag_document(tag)
						if existing_tag:
							if poem_document["_id"] not in existing_tag["publishes"]:
								existing_tag["publishes"].append(poem_document["_id"])
								existing_tag["publishes_count"] = len(existing_tag["publishes"])
								update_tag_document(existing_tag)
							poem_document[attribute].append(existing_tag["_id"])
						else:
							tag_data = Tag(tag)
							existing_tag = _Tag(**tag_data)
							existing_tag.publishes.append(poem_document["_id"])
							existing_tag.publishes_count = len(existing_tag.publishes_count)
							existing_tag.save()
							poem_document[attribute].append(existing_tag._id)
				# TODO: Annotations edits will go here
	
	is_poem_saved = update_poem_document(poem_changes=poem_document)
	if is_poem_saved:
		return Response(200).to_json()
	else:
		return Response(500, reason="Something went wrong while saving your poem.").to_json()
	

def react_to_poem(poem_id, reaction):
	auth_data = g.my_request_var["payload"]
	reactor = get_from_collection(search_value=auth_data["email_address"], search_key="email_address", collection_name="accounts")
	if reactor:
		poem = get_poem_document(poem_id)
		if poem:
			reactor_id = bson.objectid.ObjectId(reactor["_id"])
			# reset the reaction state of the user, if any
			if reactor_id in poem["likes"]:
				poem["likes"].remove(reactor_id)
				poem["likes_count"] = len(poem["likes"])
			elif reactor_id in poem["dislikes"]:
				poem["dislikes"].remove(reactor_id)
				poem["dislikes_count"] = len(poem["dislikes"])

			if reaction == "like":
				poem["likes"].append(reactor_id)
				poem["likes_count"] = len(poem["likes"])
			elif reaction == "dislike":
				poem["dislikes"].append(reactor_id)
				poem["dislikes_count"] = len(poem["dislikes"])

			is_poem_saved = update_poem_document(poem_changes=poem)
			if is_poem_saved:
				return Response(200).to_json()
			else:
				return Response(500, reason="Something went wrong while saving the poem.").to_json()
		else:
			return Response(404, reason="Poem was not found in record. It may have been deleted.").to_json()
	else:
		return Response(404, reason="Your account was not found in record.").to_json()


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
				return Response(500, reason="Something went wrong while saving the comment.")
		else:
			return Response(404, reason="Comment was not found in record.").to_json()
	else:
		return Response(404, reason="Your account was not found in record.").to_json()