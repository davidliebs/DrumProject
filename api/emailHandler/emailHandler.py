from flask import Blueprint, jsonify, request, current_app
from flask_mail import Mail, Message
from models import returnDBConnection, authenticate_token

from dotenv import load_dotenv
import os
import uuid
from datetime import datetime, timedelta

load_dotenv()

emailHandler_bp = Blueprint('emailHandler_bp', __name__)

@emailHandler_bp.route("/send_verification_email", methods=["GET"])
def send_verification_email():
	if not authenticate_token(request.headers):
		return "Invalid API key", 403
	
	conn, cur = returnDBConnection()
	
	userID = request.args.get("userID")

	# fetching users email
	cur.execute(f"SELECT userEmail FROM users WHERE userID='{userID}'")
	userEmail = cur.fetchone()[0]

	# create random token associated with their userID
	random_token = str(uuid.uuid4())
	ttl = (datetime.now() + timedelta(days=1)).timestamp()

	cur.execute(f"""
		INSERT INTO userEmailVerification
		VALUES ('{random_token}', '{userID}', '{ttl}')
	""")

	verify_email_url = os.getenv("website_base_url") + "/user/verify_email?token=" + random_token

	msg = Message('BeatBuddy - Verify your email', sender=os.getenv("mail_username"), recipients=[userEmail])
	msg.body = f"Thanks for signing up to BeatBuddy, to verify your email, click the link - {verify_email_url}"
	
	mail = Mail(current_app)
	mail.send(msg)

	conn.commit()
	conn.close()

	return jsonify(random_token)

@emailHandler_bp.route("/send_forgot_password_email", methods=["POST"])
def send_forgot_password_email():
	if not authenticate_token(request.headers):
		return "Invalid API key", 403
	
	conn, cur = returnDBConnection()

	userID = request.json.get("userID")
	userEmail = request.json.get("userEmail")

	# insert into database random token with ttl
	random_token = str(uuid.uuid4())
	ttl = (datetime.now() + timedelta(days=1)).timestamp()

	cur.execute(f"INSERT INTO userEmailVerification VALUES('{random_token}', '{userID}', '{ttl}')")
	conn.commit()

	verify_email_url = os.getenv("website_base_url") + "/user/reset-password?token=" + random_token

	msg = Message('BeatBuddy - Reset password', sender=os.getenv("mail_username"), recipients=[userEmail])
	msg.body = f"Click the link to reset your password, this link expires in 24 hours - {verify_email_url}"
	
	mail = Mail(current_app)
	mail.send(msg)

	return jsonify(random_token)