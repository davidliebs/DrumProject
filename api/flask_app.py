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

@app.route("/user/request_music_notation_data")
def request_music_notation_data():
	challengeId = request.args.get("challengeId")
	filename = challengeId + ".mid"

	music_notation_data = midi_file_library.return_formatted_midi_notes(os.path.join("./static/media", filename))

	return jsonify(music_notation_data)

@app.route("/user/serve_challenge_svg")
def serve_challenge_svg():
	challengeId = request.args.get("challengeId")
	filename = challengeId + ".svg"

	return send_from_directory("./static/media", filename)

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