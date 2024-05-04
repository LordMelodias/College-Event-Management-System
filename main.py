from flask import Flask, render_template, request, session, url_for, redirect, flash, send_from_directory, make_response
from flask_mail import Mail, Message
import json
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os.path
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.mime.text import MIMEText
import base64
import secrets
import random
from sqlalchemy import func
from werkzeug.utils import secure_filename
from flask_bcrypt import Bcrypt
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from io import BytesIO

app = Flask(__name__)

# json file for about page
with open('config.json', 'r') as c:
    params = json.load(c)["params"]

with open('config2.json', 'r') as c:
    param = json.load(c)["param"]

with open('config3.json', 'r') as c:
    regevent = json.load(c)["regevent"]  

# starting page
@app.route("/")
def home():
    return render_template('index.html')

@app.route("/about")
def about():
    return render_template('about.html', param=param)
