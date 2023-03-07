from flask import Blueprint, jsonify, request
from models import returnDBConnection, authenticate_token

from dotenv import load_dotenv
import os

load_dotenv()

userInfo_bp = Blueprint('userInfo_bp', __name__)

@userInfo_bp.route("/get_user_details", methods=["GET"])
def get_user_details():
	if not authenticate_token(request.headers):
		return "Invalid API key", 403

	conn, cur = returnDBConnection()

	userID = request.args.get("userID")

	cur.execute(f"""
		SELECT userPaid, userEmailVerified, userEmail FROM users WHERE userID = '{userID}'
	""")

	userDetails = cur.fetchone()

	conn.close()

	return jsonify(userDetails)

@userInfo_bp.route("/get_available_courses")
def get_available_courses():
	if not authenticate_token(request.headers):
		return "Invalid API key", 403

	conn, cur = returnDBConnection()

	userID = request.args.get("userID")

	cur.execute(f"""
		SELECT * FROM courses WHERE courseID IN (SELECT courseID FROM coursesEnrolled WHERE userID = '{userID}')
	""")

	courses_enrolled = cur.fetchall()

	cur.execute(f"""
		SELECT * FROM courses WHERE courseID NOT IN (SELECT courseID FROM coursesEnrolled WHERE userID = '{userID}')
	""")

	other_courses = cur.fetchall()

	cur.execute(f"""
		SELECT coursesEnrolled.courseID, (coursesEnrolled.lastChallengeCompleted / courses.courseNoChallenges * 100)
		FROM coursesEnrolled
		INNER JOIN courses
		ON coursesEnrolled.userID='{userID}'
	""")

	user_progress = {i[0]: i[1] for i in cur.fetchall()}

	data_to_return = {
		"courses enrolled": courses_enrolled,
		"other courses": other_courses,
		"user progress": user_progress
	}

	conn.close()

	return jsonify(data_to_return)

@userInfo_bp.route("/subscribe_to_newsletter", methods=["POST"])
def subscribe_to_newsletter():
	if not authenticate_token(request.headers):
		return "Invalid API key", 403

	conn, cur = returnDBConnection()

	email = request.json.get("email")
	subscribe = request.json.get("subscribe")

	if subscribe == "yes":
		cur.execute(f"INSERT INTO newsletter VALUES('{email}')")
	elif subscribe == "no":
		cur.execute(f"DELETE FROM newsletter WHERE email='{email}'")
	
	conn.commit()
	conn.close()

	return jsonify(True)