from flask import Blueprint, jsonify
from models import returnDBConnection, authenticate_token

import blob_storage_library
import process_challenge_files

from dotenv import load_dotenv
import os

load_dotenv()

creator_bp = Blueprint('creator_bp', __name__, static_folder='static', static_url_path='assets')

bucket = blob_storage_library.returnBucket()

@creator_bp.route("/create_course_entry", methods=["POST"])
def create_course_entry():
	if not authenticate_token(request.headers):
		return "Invalid API key", 403

	conn, cur = returnDBConnection()

	data = request.json

	if not data.get("courseID", False):
		course_id = str(uuid.uuid4())
	else:
		course_id = data["courseID"]

	cur.execute(f"""
		INSERT INTO courses
		VALUES ('{course_id}', '{data["courseName"]}', '{data["courseDescription"]}', '{data["courseNoChallenges"]}')
		ON DUPLICATE KEY UPDATE
		courseName='{data["courseName"]}', courseDescription='{data["courseDescription"]}', courseNoChallenges='{data["courseNoChallenges"]}'
	""")

	conn.commit()
	conn.close()

	return jsonify(courseID)

@creator_bp.route("/upload_course_logo", methods=["POST"])
def upload_course_logo():
	if not authenticate_token(request.headers):
		return "Invalid API key", 403

	courseID = request.args.get("courseID")
	course_logo_file = request.files["course_logo"]

	course_logo_file.save(os.path.join(os.getenv("course_logo_upload_path"), courseID+".png"))

	return "Successful"

@creator_bp.route("/create_challenge_entry", methods=["POST"])
def create_challenge_entry():
	if not authenticate_token(request.headers):
		return "Invalid API key", 403

	conn, cur = returnDBConnection()
	
	data = request.json

	if not data.get("challengeID", False):
		challengeID = str(uuid.uuid4())
	else:
		challengeID = data["challengeID"]

	cur.execute(f"""
		INSERT INTO challenges (challengeID, courseID, challengeNo, challengeTitle, challengeMessage)
		VALUES ('{challengeID}', '{data["courseID"]}', '{data["challengeNo"]}', '{data["challengeTitle"]}', '{data["challengeMessage"]}')
		ON DUPLICATE KEY UPDATE
		challengeNo='{data["challengeNo"]}', challengeTitle='{data["challengeTitle"]}', challengeMessage='{data["challengeMessage"]}'
	""")

	conn.commit()
	conn.close()

	return jsonify(challengeID)

@creator_bp.route("/process_challenge_svg_file", methods=["POST"])
def process_challenge_svg_file():
	if not authenticate_token(request.headers):
		return "Invalid API key", 403

	conn, cur = returnDBConnection()

	svg_filepath = "./static/challenge.svg"

	challengeID = request.args.get("challengeID")
	challengeSVGFile = request.files.get("challengeSVGFile")
	challengeSVGFile.save(svg_filepath)

	fileURL = blob_storage_library.uploadFileToBucket(b2_api, bucket, svg_filepath, challengeID+".svg")
	svgIndexes = json.dumps(process_challenge_files.return_svg_indexes(svg_filepath))

	os.remove(svg_filepath)

	cur.execute(f"""
		UPDATE challenges
		SET svgIndexes='{svgIndexes}', challengeSvgURL='{fileURL}'
		WHERE challengeID = '{challengeID}'
	""")

	conn.commit()
	conn.close()

	return "Successful"

@creator_bp.route("/process_challenge_midi_file", methods=["POST"])
def process_challenge_midi_file():
	if not authenticate_token(request.headers):
		return "Invalid API key", 403

	conn, cur = returnDBConnection()

	midi_filepath = "./static/challenge.mid"

	challengeID = request.args.get("challengeID")
	challengeMIDIFile = request.files.get("challengeMIDIFile")

	challengeMIDIFile.save(midi_filepath)

	music_data = json.dumps(process_challenge_files.return_formatted_midi_notes(midi_filepath))

	os.remove(midi_filepath)

	cur.execute(f"""
		UPDATE challenges
		SET musicData='{music_data}'
		WHERE challengeID = '{challengeID}'
	""")

	conn.commit()
	conn.close()

	return "Successful"

@creator_bp.route("/fetch_courses", methods=["GET"])
def fetch_courses():
	if not authenticate_token(request.headers):
		return "Invalid API key", 403

	conn, cur = returnDBConnection()

	cur.execute("SELECT courseID FROM courses")
	data = [i[0] for i in cur.fetchall()]

	conn.close()

	return jsonify(data)

@creator_bp.route("/fetch_course_information", methods=["GET"])
def fetch_course_information():
	if not authenticate_token(request.headers):
		return "Invalid API key", 403

	conn, cur = returnDBConnection()

	courseID = request.args.get("courseID")

	data = {}

	cur.execute(f"SELECT courseID, courseName, courseDescription, courseNoChallenges FROM courses WHERE courseID='{courseID}'")
	data["course_info"] = cur.fetchone()

	cur.execute(f"""
		SELECT challengeID, courseID, challengeNo, challengeTitle, challengeMessage 
		FROM challenges 
		WHERE courseID='{courseID}'
	""")

	data["challenges"] = {i[2]: i for i in cur.fetchall()}

	conn.close()

	return jsonify(data)

@creator_bp.route("/delete_course", methods=["GET"])
def delete_course():
	if not authenticate_token(request.headers):
		return "Invalid API key", 403

	conn, cur = returnDBConnection()

	courseID = request.args.get("courseID")

	cur.execute(f"DELETE FROM courses WHERE courseID='{courseID}'")
	cur.execute(f"DELETE FROM challenges WHERE courseID='{courseID}'")
	cur.execute(f"DELETE FROM coursesEnrolled WHERE courseID='{courseID}'")

	conn.commit()
	conn.close()

	return "Successful"