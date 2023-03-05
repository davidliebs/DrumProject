from flask import Flask

from challenge.challenge import challenge_bp
from course.course import course_bp
from creator.creator import creator_bp
from payment.payment import payment_bp
from userAuth.userAuth import userAuth_bp
from userInfo.userInfo import userInfo_bp
from emailHandler.emailHandler import emailHandler_bp

from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

app.register_blueprint(challenge_bp, url_prefix='/challenge')
app.register_blueprint(course_bp, url_prefix='/course')
app.register_blueprint(creator_bp, url_prefix='/creator')
app.register_blueprint(payment_bp, url_prefix='/payment')
app.register_blueprint(userAuth_bp, url_prefix='/userAuth')
app.register_blueprint(userInfo_bp, url_prefix='/userInfo')
app.register_blueprint(emailHandler_bp, url_prefix='/emailHandler')

app.config['MAIL_SERVER'] = os.getenv("mail_server")
app.config['MAIL_PORT'] = int(os.getenv("mail_port"))
app.config['MAIL_USERNAME'] = os.getenv("mail_username")
app.config['MAIL_PASSWORD'] = os.getenv("mail_password")
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True