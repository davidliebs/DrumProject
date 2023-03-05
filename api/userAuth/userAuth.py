from flask import Blueprint, jsonify
from models import returnDBConnection, authenticate_token

import bcrypt
from dotenv import load_dotenv
import os

load_dotenv()

userAuth_bp = Blueprint('userAuth_bp', __name__)

@userAuth_bp.route("/login", methods=["POST"])
def user_login():
	if not authenticate_token(request.headers):
		return "Invalid API key", 403

	conn, cur = returnDBConnection()

	login_data = request.json

	cur.execute(f"""
		SELECT userID, userPassword, userAdmin FROM users
		WHERE userEmail = '{login_data["userEmail"]}'
	""")
	returned_data = cur.fetchone()

	conn.close()

	if returned_data == None:
		return jsonify("Incorrect")

	if bcrypt.checkpw(login_data["userPassword"].encode(), returned_data[1].encode()):
		return jsonify({"userID": returned_data[0], "userAdmin": returned_data[2]})
	else:
		return jsonify("Incorrect")

@userAuth_bp.route("/signup", methods=["POST"])
def user_signup():
	if not authenticate_token(request.headers):
		return "Invalid API key", 403

	conn, cur = returnDBConnection()

	signup_data = request.json

	userID = str(uuid.uuid4())
	hashed_password = bcrypt.hashpw(signup_data["userPassword"].encode(), bcrypt.gensalt()).decode()

	cur.execute(f"""
		INSERT INTO users
		VALUES ('{userID}', '{signup_data["userEmail"]}', '{hashed_password}', 0, 0, 0)
	""")

	conn.commit()
	conn.close()

	# sending email verification
	requests.get(f"{os.getenv('api_base_url')}/user/send_verification_email", params={"userID": userID}, headers={"Authorisation": os.getenv("beatbuddy_api_key")})

	return jsonify(userID)

@userAuth_bp.route("/send_verification_email", methods=["GET"])
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
	mail.send(msg)

	conn.commit()
	conn.close()

	return jsonify(random_token)

@userAuth_bp.route("/verify_email", methods=["GET"])
def verify_email():
	if not authenticate_token(request.headers):
		return "Invalid API key", 403

	conn, cur = returnDBConnection()

	token = request.args.get("token")

	cur.execute(f"""
		SELECT * FROM userEmailVerification WHERE token = '{token}'
	""")
	data = cur.fetchall()

	if data == []:
		return jsonify("There was a problem finding your email, click resend on the homepage")
	
	if float(data[0][2]) < datetime.now().timestamp():
		return jsonify("The link sent to you has expired, click resend on the homepage")
	
	if token == data[0][0]:
		cur.execute(f"UPDATE users SET userEmailVerified=1 WHERE userID='{data[0][1]}'")
		conn.commit()
		conn.close()

		return jsonify("Successful")
	
	conn.close()
	return jsonify("There was a problem finding your email, click resend on the homepage")

@userAuth_bp.route("/change_email", methods=["GET"])
def change_email():
	if not authenticate_token(request.headers):
		return "Invalid API key", 403

	conn, cur = returnDBConnection()

	userID = request.args.get("userID")
	newEmail = request.args.get("newEmail")

	cur.execute(f"""
		UPDATE users SET userEmail='{newEmail}', userEmailVerified=0
		WHERE userID = '{userID}'
	""")

	conn.commit()
	conn.close()

	return jsonify("Successful")

@userAuth_bp.route("/change_password", methods=["POST"])
def change_password():
	if not authenticate_token(request.headers):
		return "Invalid API key", 403

	conn, cur = returnDBConnection()

	data = request.json

	hashed_password = bcrypt.hashpw(data["newPassword"].encode(), bcrypt.gensalt()).decode()

	cur.execute(f"""
		UPDATE users SET userPassword = '{hashed_password}'
	""")

	conn.commit()
	conn.close()

	return jsonify("Successful")

@userAuth_bp.route("/delete_account", methods=["GET"])
def delete_account():
	if not authenticate_token(request.headers):
		return "Invalid API key", 403
	
	conn, cur = returnDBConnection()
	
	userID = request.args.get("userID")

	cur.execute(f"DELETE FROM users WHERE userID = '{userID}'")
	cur.execute(f"DELETE FROM coursesEnrolled WHERE userID = '{userID}';")

	conn.commit()
	conn.close()

	return jsonify("Successful")
