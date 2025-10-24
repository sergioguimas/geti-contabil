from flask import Flask
import re
import os
import os.path
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime
load_dotenv()

KEY_FLASK = os.getenv("KEY_FLASK")

app = Flask(__name__)
app.secret_key = KEY_FLASK

#Função para formatar data
@app.template_filter('format_datetime')
def format_datetime_filter(iso_string):
    if not iso_string:
        return "N/A"
    try:
        dt = datetime.fromisoformat(re.sub(r'Z$', '+00:00', iso_string))
        return dt.strftime('%d/%m/%Y %H:%M')
    except ValueError:
        return iso_string

#Função para formatar Tipo do Arquivo
@app.template_filter('format_mimetype')
def format_mimetype_filter(mime_type):
    if not mime_type:
        return "Desconhecido"
    
    if mime_type == 'application/vnd.google-apps.folder':
        return 'Pasta'
    if 'xml' in mime_type:
        return 'Arquivo XML'
    if 'pdf' in mime_type:
        return 'Arquivo PDF'
    if 'spreadsheet' in mime_type or 'excel' in mime_type or 'csv' in mime_type:
        return 'Planilha'
    if 'document' in mime_type or 'word' in mime_type:
        return 'Documento'
    if 'presentation' in mime_type or 'powerpoint' in mime_type:
        return 'Apresentação'
    if 'image' in mime_type:
        return 'Imagem'
    if 'zip' in mime_type or 'archive' in mime_type:
        return 'Arquivo ZIP'
    
    return 'Arquivo'

from routes import *

if __name__ == "__main__":
    app.run()