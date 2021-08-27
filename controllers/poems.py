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
from models.draft import Draft


# helpers
from helpers.request import read_request_body
from helpers.poems import get_poem_document, update_poem_document, get_tag_document, update_tag_document
from helpers.database import get_from_collection, update_a_document, delete_documents


# schema
from schemas.tag import Tag as _Tag
from schemas.poem import Poem as _Poem
from schemas.draft import Draft as _Draft


"""""""""PUBLISHING POEMS"""""""""
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


"""""""""EDITING POEMS"""""""""
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
	

"""""""""DELETING POEMS"""""""""
def delete_poem(poem_id):
	auth_data = g.my_request_var["payload"]
	account = get_from_collection(search_value=auth_data["email_address"], search_key="email_address", collection_name="accounts")
	poem_id = bson.objectid.ObjectId(poem_id)
	
	if account:
		poem = get_poem_document(str(poem_id))
		if poem:
			if account["_id"] == poem["author"]:
				is_poem_deleted = delete_documents(search_value=poem_id, search_key="_id", collection_name="poems")
				if is_poem_deleted:
					# also delete the comments the were made for the poem
					is_comments_deleted = delete_documents(search_value=poem_id, search_key="of", collection_name="comments")
					if is_comments_deleted:
						return Response(200).to_json()
					else:
						return Response(500, reason="Something went while deleting comments in the poem.").to_json()
				else:
					return Response(500, reason="Something went wrong while deleting poem.").to_json()
			else:
				return Response(403, reason="You are not allowed to carry-out this action.").to_json()
		else:
			return Response(404, reason="Poem was not found in record.").to_json()
	else:
		return Response(404, reason="Your account was not found in record.").to_json()
	

"""""""""REACTING TO POEMS"""""""""
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


# Be able to rank poems from the most liked to the most disliked for a user that is not logged in
def unauthenticated_poemsfeed():
	poems = get_from_collection(search_value=None, collection_name="poems", return_all=True)
	recommended_poems = []

	# rank the poems
	for poem in poems:
		# recommend a poem if the likes are more than the dislikes, with an offset difference of 20
		if poem["likes_count"] > (poem["dislikes_count"] - 20):
			recommended_poems.append(poem)

	# if the recommended_poems has no items, return all poems
	if len(recommended_poems) == 0:
		recommended_poems = poems

	# prepare the response
	for index, poem in enumerate(recommended_poems):
		recommended_poems[index] = Poem.to_dict(recommended_poems[index])
		recommended_poems[index]["_id"] = str(recommended_poems[index]["_id"])
		recommended_poems[index]["author"] = str(recommended_poems[index]["author"])

	return Response(200, data=recommended_poems).to_json()


"""DRAFTING POEMS"""
def create_a_draft():
	auth_data = g.my_request_var["payload"]
	author = get_from_collection(search_value=auth_data["email_address"], search_key="email_address", collection_name="accounts")
	if author:
		request_data = read_request_body(request=request)
		if request_data:
			draft = get_from_collection(search_value=request_data.get("did"), search_key="did", collection_name="drafts")
			if draft:
				print("Draft exists.")
				draft = { **draft, **request_data }
				print(draft["title"], draft["body"], request_data)
				is_draft_saved = update_a_document(document_changes=draft, collection_name="drafts")
				if is_draft_saved:
					return Response(200).to_json()
				else:
					return Response(500, reason="Something went wrong while saving the draft.")
			else:
				print("New draft.")
				draft_data = Draft(request_data)
				draft = _Draft(**draft_data.__dict__)
				author["drafts"].append(draft._id)
				is_author_saved = update_a_document(document_changes=author, collection_name="accounts")
				print(is_author_saved)
				if is_author_saved:
					draft.save()
					return Response(200).to_json()
				else:
					return Response(500, reason="Something went wrong while saving the draft.").to_json()
		else:
			return Response(400, reason="Incomplete request. No data was received.").to_json()
	else:
		return Response(403, reason="You are not allowed to carry out this action.").to_json()


"""GETTING A DRAFT POEM"""
def get_a_draft(did: str) -> str:
	auth_data = g.my_request_var["payload"]
	author = get_from_collection(search_value=auth_data["email_address"], search_key="email_address", collection_name="accounts")
	if author:
		draft_document = get_from_collection(search_value=did, search_key="did", collection_name="drafts")
		print(draft_document)
		if draft_document:
			draft_document = Poem.to_dict(draft_document)
			return Response(200, data=draft_document).to_json()
		else:
			return Response(404, reason="Draft does not exist in record.").to_json()
	else:
		return Response(404, reason="Original author was not found in record.").to_json()