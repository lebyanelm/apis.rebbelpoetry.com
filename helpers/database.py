import os
import sys
import traceback
import mongoengine


def get_from_collection(search_value: str, collection_name="acccounts", search_key="_id"):
	collection = mongoengine.get_connection().get_database(os.environ["DATABASE_NAME"]).get_collection(collection_name)
	cursor = collection.find({ search_key : search_value })
	result = None

	print(cursor.count(), "cur")
	if cursor:
		for _result in cursor:
			result = _result
			break

	return result


def update_a_document(document_changes, collection_name="accounts"):
	try:
		collection = mongoengine.get_connection().get_database(os.environ["DATABASE_NAME"]).get_collection(collection_name)

		document_object_id = document_changes["_id"]
		del document_changes["_id"]

		collection.find_one_and_update(
			{ "_id" : document_object_id },
			{ "$set" : document_changes }
		)

		document_changes["_id"] = document_object_id

		return True
	except:
		error = traceback.format_exc()
		print(error)
		
		return False