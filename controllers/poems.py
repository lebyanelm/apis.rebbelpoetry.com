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


def publish_a_poem():
	request_data = read_request_body(request)
	poem = Poem(request_data)

	# from the poem, also try to extract some tags from the data provided.
	# when the tags were provided by the author use them to make tags, else extract them from the body
	# try to extract them from the data items provided by the author
	
	
	# make a tag on the database
	for tag in poem.tags:
		tag_data = get_tag(tag)
		
		if tag_data == None:
			tag = Tag(tag)

			tag.publishes.append(poem.id)
			tag.publishes_count = 1
			
			tag_schema = _Tag(**tag.__dict__)
			tag_schema.save()
		else:
			tag_data["publishes"].append(poem.id)
			tag_data["publishes_count"] += 1

			# save the updated tag
			update_tag(tag_data)
	
	return Response(200).to_json()

