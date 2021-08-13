import os
import bson
import mongoengine


from helpers.database import get_from_collection, update_a_document


def parse_poem_tags_string(tags):
	_tags = []
	if (type(tags) == str):
		_tags_split = tags.rsplit(',')
		for _tag_split in _tags_split:
			_tags.append(_tag_split.strip().lower())
	elif type(tags) == list:
		_tags = tags
	return _tags


def get_poem_document(poem_id: str):
	poem_document = get_from_collection(search_value=bson.objectid.ObjectId(poem_id), search_key="_id", collection_name="poems")
	return poem_document


def update_poem_document(poem_changes):
	return update_a_document(document_changes=poem_changes, collection_name="poems")


def get_tag_document(tag_name: str):
	tag_document = get_from_collection(search_value=tag_name, search_key="name", collection_name="tags")
	return tag_document


def update_tag_document(tag_changes):
	return update_a_document(tag_changes, collection_name="tags")