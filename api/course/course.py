from flask import Blueprint, jsonify
from models import returnDBConnection, authenticate_token

from dotenv import load_dotenv
import os

load_dotenv()

course_bp = Blueprint('course_bp', __name__)

@course_bp.route("/enroll_course")
def enroll_course():
	if not authenticate_token(request.headers):
		return "Invalid API key", 403

	conn, cur = returnDBConnection()

	userID = request.args.get("userID")
	courseID = request.args.get("courseID")
	userPaid = request.args.get("userPaid")

	if userPaid == "0":
		cur.execute(f"SELECT courseID FROM coursesEnrolled WHERE userID='{userID}'")
		numberCoursesEnrolled = len(cur.fetchall())

		if numberCoursesEnrolled >= int(os.getenv("num_courses_allowed_on_free_plan")):
			conn.close()

			return jsonify("Limit reached")

	cur.execute(f"""
		INSERT INTO coursesEnrolled
		VALUES ('{userID}', '{courseID}', 0) 
	""")

	conn.commit()
	conn.close()

	return jsonify("Success")