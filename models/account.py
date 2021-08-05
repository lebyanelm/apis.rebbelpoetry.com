# dependencies
import nanoid
import json
import os
from models.data import Data


class Account(Data):
	def __init__(self, data):
		super().__init__()

		self.display_name = data['display_name']
		self.email_address = data['email_address']
		self.password = data['password']

		if data.get('display_photo') is None:
			if os.environ['ENVIRONMENT'] == os.environ['DEVELOPMENT_MODE']:
				sub_url = os.environ['DEV_API_ENDPOINT'] 
			else:
				sub_url = os.environ['PROD_API_ENDPOINT']
			self.display_photo = '/'.join([sub_url, 'uploads', 'default-avatar.png'])
		else:
			self.display_photo = data['display_photo']

		if data.get('poems') is None:
			self.poems = []
		else:
			self.poems = data['poems']

		if data.get('archived_poems') is None:
			self.archived_poems = []
		else:
			self.archived_poems = data['archived_poems']

		if data.get('bookmarked_poems') is None:
			self.bookmarked_poems = []
		else:
			self.bookmarked_poems = data['bookmarked_poems']

		if data.get('recent_searches') is None:
			self.recent_searches = []
		else:
			self.recent_searches = data['recent_searches']

		if data.get('followers') is None:
			self.followers = []
		else:
			self.followers = data['followers']

		if data.get('follows') is None:
			self.follows = []
		else:
			self.follows = data['follows']

		if data.get('biography') is None:
			self.biography = ""
		else:
			self.biography = data['biography']

		if data.get('drafts') is None:
			self.drafts = []
		else:
			self.drafts = data['drafts']

		if data.get('verification_codes') is None:
			self.verification_codes = []
		else:
			self.verification_codes = data['verification_codes']

		if data.get('notifications') is None:
			self.notifications = []
		else:
			self.notifications = data['notifications']


	def to_json(self) -> str:
		return json.dumps(obj=self.__dict__)