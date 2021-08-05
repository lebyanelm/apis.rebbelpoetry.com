# dependencies
import os
import mongo_connection
from dotenv import dotenv_values
from flask import Flask, request, send_file
from flask_cors import CORS, cross_origin


# models
import models.response


# controllers
import controllers.accounts as AccountsController


####### SERVER ENVIRONMENTAL VARIABLES SETUP ##########
config = { **dotenv_values('.env.shared') }

if config['ENVIRONMENT'] == config['DEVELOPMENT_MODE']:
	config = { **config, **dotenv_values('.env.secret') }

os.environ = {
	**os.environ,
	**config
}



###### MAKE A DATABASE CONNECTION ########
mongodb_client = mongo_connection.create_mongodb_connection(os.environ['ENVIRONMENT'])



####### START A SERVER AND API ROUTES ########
server = Flask(__name__, static_folder="./uploads/", static_url_path="/api/uploads/")
CORS(server, resources={ r"*": { "origins": "*" } })



########## ACCOUNT FACILITATION AND USER MANAGEMENT ##########
@server.route("/api/accounts", methods=["POST", "PUT"])
@cross_origin()
def create_user_account() -> str:
	return AccountsController.create_user_account()
	



######### SET THE SERVER TO RUN #########
IS_DEBUG_MODE = os.environ["ENVIRONMENT"] == os.environ["DEVELOPMENT_MODE"]
server.run(debug=IS_DEBUG_MODE, host="0.0.0.0")
