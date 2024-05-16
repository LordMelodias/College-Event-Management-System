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

# json file for about page
with open('config.json', 'r') as c:
    params = json.load(c)["params"]

with open('config2.json', 'r') as c:
    param = json.load(c)["param"]

with open('config3.json', 'r') as c:
    regevent = json.load(c)["regevent"]  

# Generate a random secret key
secret_key = secrets.token_hex(16)

# Function to get Gmail API credentials
def get_gmail_credentials():
    SCOPES = ['https://www.googleapis.com/auth/gmail.send']
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json')
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'path/to/client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

# Function to create a MIME message
def create_message(sender, to, subject, body):
    message = MIMEText(body)
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    return {'raw': raw_message}

# Function to send a message using Gmail API
def send_message(service, user_id, message):
    try:
        message = service.users().messages().send(userId=user_id, body=message).execute()
        print(f"Message Id: {message['id']}")
        return message
    except HttpError as error:
        print(f"An error occurred: {error}")


# Initialize the Flask application
app = Flask(__name__)
app.config['upload_image'] = 'C:/xampp/htdocs/valia/static/img/upload_image/'
app.config['uploads_event'] = 'C:/xampp/htdocs/valia/static/img/uploads_event/'
app.config['upload_schedule'] = 'C:/xampp/htdocs/valia/static/img/upload_schedule/'
app.config['upload_sponsors'] = 'C:/xampp/htdocs/valia/static/img/upload_sponsors/'

# for contact form
local_server = True
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params['gmail-user'],
    MAIL_PASSWORD=params['gmail-password']
)

# Create a single instance of SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/XYZ'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = secret_key
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'rohit######@######'  # Update with your Gmail email
app.config['MAIL_PASSWORD'] = 'h##############'  # Update with your Gmail password

db = SQLAlchemy(app)
mail = Mail(app)

class Contact(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(20), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    subject = db.Column(db.String(12), nullable=False)
    message = db.Column(db.String(120), nullable=False)

# Define the Event model
class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)  # New column for time
    description = db.Column(db.Text, nullable=False)
    photo_path = db.Column(db.String(255), nullable=True)

# Define Participant model
class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    college = db.Column(db.String(100))
    event_title = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)  # Ensure email uniqueness
    phone = db.Column(db.String(20), nullable=False, unique=True)   # Ensure phone uniqueness

class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.Integer)
    time = db.Column(db.Time)
    event_name = db.Column(db.String(100))
    event_image = db.Column(db.String(255))
    title = db.Column(db.String(100))
    description = db.Column(db.Text)

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)

# Add this new model for sponsors
class Sponsors(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)

# funtion for uploading.....
def get_uploaded_images():
    return Image.query.all()

def get_uploaded_event():
    return Event.query.all()

def get_uploaded_schedule():
    return Schedule.query.all()

# Route to handle form submission
@app.route('/submit_form', methods=['POST'])
def submit_form():
    if request.method == 'POST':
        # Get form data
        first_name = request.form['firstName']
        last_name = request.form['lastName']
        college = request.form['organization']
        event_title = request.form['title']
        email = request.form['email']
        phone = request.form['phone']
        

        # Create a new Entry object and add it to the database session
        new_entry = Entry(
            first_name=first_name,
            last_name=last_name,
            college=college,
            event_title=event_title,
            email=email,
            phone=phone
        )
        db.session.add(new_entry)
        db.session.commit()
        subject = 'Confirmation of Event Registration'
        body = f'Dear {first_name},\n\nThank you for registering for the event "{event_title}". We look forward to seeing you there!\n\nBest regards,\nThe Event Team'
        msg = Message(subject, sender='rohitchauhan9880@email@gmail.com', recipients=[email])
        msg.body = body
        mail.send(msg)
        # Optionally, you can return a response or redirect to another page
        return render_template('successful.html', participant=new_entry)


# starting page
@app.route("/")
def home():
    return render_template('index.html')

@app.route("/event")
def event():
    events = Event.query.all()
    return render_template("event.html", events=events)

@app.route("/about")
def about():
    return render_template('about.html', param=param)

@app.route("/regform")
def regform():
    return render_template("regform.html", regevent=regevent)

# Schedule Event 
@app.route("/schedule")
def schedule():
    selected_day = request.args.get('day', default=1, type=int)
    schedules = Schedule.query.all()
    print("Selected Day:", selected_day)
    print("Retrieved Schedules:", schedules)
    return render_template("schedule.html", schedules=schedules, selected_day=selected_day)

# term and condition
@app.route("/term")
def term():
    return render_template("term.html")

# Gallery Display
@app.route("/gallery")
def gallery():
    images = Image.query.all()
    return render_template("gallery.html", images=images)

# event 2020
@app.route("/2020")
def past2020():
    return render_template('2020.html')