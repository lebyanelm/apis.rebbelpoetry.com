# dependencies
import os
import sys
import mongoengine
from flask import request


# models
from models.poem import Poem
from models.response import Response
from models.tag import Tag

# helpers
from helpers.request import read_request_body
from helpers.poems import get_tag, update_tag

# schema
from schemas.tag import Tag as _Tag
from schemas.account import Account as _Account
from schemas.poem import Poem as _Poem


def publish_a_poem():
	request_data = read_request_body(request)
	poem_data = Poem(request_data).__dict__
	poem = _Poem(**poem_data)

	# save the tags on the database to be used for searching
	for index, tag in enumerate(poem.tags):
		tag_data = get_tag(tag)
		
		if tag_data == None:
			tag = Tag(tag)

			tag.publishes.append(poem.id)
			tag.publishes_count = 1
			
			tag_schema = _Tag(**tag.__dict__)
			poem.tags[index] = tag_schema._id
			tag_schema.save()
		else:
			tag_data["publishes"].append(poem.id)
			tag_data["publishes_count"] += 1

			poem.tags[index] = tag_data["_id"]

			# save the updated tag
			update_tag(tag_data)

	poem.save()
	poem_data["_id"] = str(poem_data["_id"])
	
	# save the account in the database and return it to the user
	return Response(200, data=poem_data).to_json()