from flask import Flask, render_template, jsonify, send_from_directory, request
from flask_cors import CORS
import json
import midi_file_library
import os
import uuid
import bcrypt
import mysql.connector

app = Flask(__name__)

conn = mysql.connector.connect(
	user = "david",
	password = "open1010",
	database = "DrumApp",
	host = "127.0.0.1",
	port = 3306
)
cur = conn.cursor()

@app.route("/user/signup", methods=["POST"])
def user_signup():
	signup_data = request.json

	userID = str(uuid.uuid4())
	hashed_password = bcrypt.hashpw(signup_data["userPassword"], bcrypt.gensalt())

	cur.execute(f"""
		INSERT INTO users
		VALUES ('{userID}', '{signup_data["userEmail"]}', '{hashed_password}')
	""")

	conn.commit()

	return jsonify(userID)

@app.route("/user/login", methods=["POST"])
def user_login():
	login_data = request.json

	cur.execute(f"""
		SELECT userID, userPassword FROM users
		WHERE userEmail = '{login_data["userEmail"]}'
	""")
	returned_data = cur.fetchone()

	if bcrypt.checkpw(login_data["userPassword"], returned_data[1]):
		return jsonify(returned_data[0])
	else:
		return jsonify("Incorrect")

@app.route("/user/get_available_courses")
def get_available_courses():
	userID = request.args.get("userID")

	# SELECT courses.courseID, courses.courseName, courses.Descr  FROM coursesEnrolled WHERE userID = '{userID}'
	cur.execute(f"""
		SELECT * FROM courses WHERE courseID IN (SELECT courseID FROM coursesEnrolled WHERE userID = '{userID}');
	""")

	courses_enrolled = cur.fetchall()

	cur.execute(f"""
		SELECT * FROM courses WHERE courseID NOT IN (SELECT courseID FROM coursesEnrolled WHERE userID = '{userID}');
	""")

	other_courses = cur.fetchall()

	data_to_return = {
		"courses enrolled": courses_enrolled,
		"other courses": other_courses
	}

	return jsonify(data_to_return)

@app.route("/user/request_music_notation_data")
def request_music_notation_data():
	courseID = request.args.get("courseID")
	challengeID = request.args.get("challengeID")

	cur.execute(f"SELECT musicData FROM challenges WHERE courseID = '{courseID}' AND challengeID = '{challengeID}'")
	music_notation_data = cur.fetchone()[0]

	return music_notation_data

@app.route("/user/serve_challenge_svg")
def serve_challenge_svg():
	courseID = request.args.get("courseID")
	challengeID = request.args.get("challengeID")

	cur.execute(f"SELECT challengeSvgFilePath FROM challenges WHERE courseID='{courseID}' AND challengeID='{challengeID}'")
	challenge_svg_filepath = cur.fetchone()[0]

	return send_from_directory(challenge_svg_filepath.replace(os.path.basename(challenge_svg_filepath), ""), os.path.basename(challenge_svg_filepath))

@app.route("/user/get_next_challengeID")
def get_next_challenge_id():
	courseID = request.args.get("courseID")
	challengeID = request.args.get("challengeID")

	if challengeID == None:
		cur.execute(f"SELECT challengeID FROM challenges WHERE courseID = '{courseID}' AND challengeNo = 1")
		nextChallengeID = cur.fetchone()
	else:
		cur.execute(f"SELECT challengeNo FROM challenges WHERE courseID = '{courseID}' AND challengeId = '{challengeID}'")
		challenge_no = cur.fetchone()[0]
		cur.execute(f"SELECT challengeID FROM challenges WHERE courseID = '{courseID}' AND challengeNo = {challenge_no+1}")
		nextChallengeID = cur.fetchone()

	if nextChallengeID == None:
		return jsonify("Finished")

	return jsonify(nextChallengeID[0])

@app.route("/user/enroll_course")
def enroll_course():
	userID = request.args.get("userID")
	courseID = request.args.get("courseID")

	cur.execute(f"""
		INSERT INTO coursesEnrolled
		VALUES ('{userID}', '{courseID}', 0) 
	""")

	conn.commit()

	return "Success"

@app.route("/user/request_midi_notes_to_drum_name")
def request_midi_notes_to_drum_name():
	data = {
		40: "snare",
		48: "high-tom",
		45: "mid-tom",
		43: "floor-tom",
		55: "crash",
		49: "crash",
		52: "crash 2",
		57: "crash 2",
		51: "ride",
		59: "ride"
	}

	return jsonify(data)

app.run(port=5000, debug=True)