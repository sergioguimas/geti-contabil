from flask import Flask
import os
from dotenv import load_dotenv
load_dotenv()

KEY_FLASK = os.getenv("KEY_FLASK")

app = Flask(__name__)
app.secret_key = KEY_FLASK

from routes import *

if __name__ == "__main__":
    app.run(debug=True)