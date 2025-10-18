from flask import Flask
import os
from dotenv import load_dotenv
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
load_dotenv()

KEY_FLASK = os.getenv("KEY_FLASK")

app = Flask(__name__)
app.secret_key = KEY_FLASK

from routes import *

if __name__ == "__main__":
    app.run(debug=True)