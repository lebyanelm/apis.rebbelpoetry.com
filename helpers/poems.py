import os
import mongoengine

def parse_poem_tags_string(tags):
	_tags = []
	if (type(tags) == str):
		_tags_split = tags.rsplit(',')
		for _tag_split in _tags_split:
			_tags.append(_tag_split.strip().lower())
	elif type(tags) == list:
		_tags = tags
	return _tags


def get_tag(tag_name: str):
	tags_collection = mongoengine.get_connection().get_database(os.environ["DATABASE_NAME"]).get_collection("tags")
	tag_cursor = tags_collection.find({ "name" : tag_name })
	tag = None

	if tag_cursor:
		for _tag in tag_cursor:
			tag = _tag
			break

	return tag


def update_tag(tag_changes):
	try:
		tags_collection = mongoengine.get_connection().get_database(os.environ["DATABASE_NAME"]).get_collection("tags")

		tag_object_id = tag_changes["_id"]
		del tag_changes["_id"]

		tags_collection.find_one_and_update(
			{ "_id" : tag_object_id },
			{ "$set" : tag_changes }
		)

		tag_changes["_id"] = tag_object_id

		return True
	except:
		print(sys.exc_info()[1])
		return False