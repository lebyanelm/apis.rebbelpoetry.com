# dependencies
import os
import sys
import nanoid
from flask import request, g
from PIL import Image


# models
from models.response import Response


# helpers
from helpers.authentication import is_authenticated
from helpers.uploads import generate_filename, get_file_extension, generate_resource_urls
from helpers.request import query_string_to_dict


# handles a file upload then creates a public url for it
def handle_resource_upload():
	if "file" in request.files and request.files["file"].filename:
		file = request.files["file"]
		request_query = query_string_to_dict(request.query_string.decode("ascii"))

		# accepted filetypes, only images and audio files
		image_types = ["image/png", "image/jpg", "image/jpeg", "image/gif"]
		audio_types = ["audio/mp3", "audio/m4a", "audio/mpeg"]
		
		if file.content_type in image_types or file.content_type in audio_types:
			filename = generate_filename()
			file_extension = get_file_extension(file.filename)

			user_upload_path = os.path.join(os.getcwd(), "uploads")
			
			if os.path.exists(user_upload_path) == False:
				os.mkdir(user_upload_path)

			file_upload_path = os.path.join(user_upload_path, filename)
			os.mkdir(file_upload_path)

			# depending on the file type, either audio save the file, image requires more processing
			if file.content_type in image_types:
				original_filepath = os.path.join(file_upload_path, "large." + file_extension)
				file.save(original_filepath)
				file.close()

				# resize the image by 50% for loading purposes, ie. for thumbnails
				image = Image.open(original_filepath)
				medium_dimensions = (int(image.size[0] * 0.5), int(image.size[1] * 0.5))
				medium_image = image.resize(medium_dimensions, Image.ANTIALIAS)

				# thumbnail path
				medium_filepath = os.path.join(file_upload_path, "medium." + file_extension)
				medium_image.save(medium_filepath)
				medium_image.close()

				# if it is an avatar image
				small_dimensions = (int(image.size[0] * 0.2), int(image.size[1] * 0.2))
				small_image = image.resize(small_dimensions, Image.ANTIALIAS)

				avatar_filepath = os.path.join(file_upload_path, "small." + file_extension)
				small_image.save(avatar_filepath)
				small_image.close()

				return Response(200, data=generate_resource_urls(file_upload_path, file_extension)).to_json()
			else:
				# if audio file, save it as audio.<extension>
				filepath = os.path.join(file_upload_path, "original." + file_extension)
				file.save(filepath)
				file.close()

				return Response(200, data=generate_resource_urls(file_upload_path, file_extension, is_audio=True)).to_json()
		else:
			return Response(400, reason="Unacceptable file type upload.").to_json()
	else:
		return Response(400, reason="No file was attached for uploading.").to_json()
	

def get_upload_resource_urls(uploaded_resource):
	resource_fpath = os.path.join(os.getcwd(), "uploads", uploaded_resource)
	if os.path.exists(resource_fpath):
		resource_files = os.listdir(resource_fpath)
		print(resource_files)
		resource_urls = dict()
		for resource_file in resource_files:
			resource_name = resource_file.rsplit(".")[0]
			resource_extension = resource_file.rsplit(".")[-1]

			if resource_extension in ["mp3", "m4a", "wav", "webm"]:
				is_audio_resource = True
			else:
				is_audio_resource = False
			
		resource_urls = generate_resource_urls(resource_path=resource_fpath, extension=resource_extension, is_audio=is_audio_resource)
		return Response(200, data=resource_urls).to_json()
	else:
		return Response(404, reason="Resource not found.").to_json()