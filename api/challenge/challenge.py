from flask import Blueprint, jsonify
from models import returnDBConnection, authenticate_token

from dotenv import load_dotenv
import os

load_dotenv()

challenge_bp = Blueprint('challenge_bp', __name__)

@challenge_bp.route("/request_music_notation_data")
def request_music_notation_data():
	if not authenticate_token(request.headers):
		return "Invalid API key", 403

	conn, cur = returnDBConnection()

	courseID = request.args.get("courseID")
	challengeID = request.args.get("challengeID")

	cur.execute(f"SELECT musicData, svgIndexes, challengeTitle, challengeMessage, challengeSvgURL FROM challenges WHERE courseID = '{courseID}' AND challengeID = '{challengeID}'")
	music_notation_data = cur.fetchone()

	conn.close()

	return jsonify(music_notation_data)

@challenge_bp.route("/get_next_challengeID")
def get_next_challenge_id():
	if not authenticate_token(request.headers):
		return "Invalid API key", 403

	conn, cur = returnDBConnection()

	userID = request.args.get("userID")
	courseID = request.args.get("courseID")
	challengeID = request.args.get("challengeID")

	cur.execute(f"SELECT lastChallengeCompleted FROM coursesEnrolled WHERE userID='{userID}' AND courseID='{courseID}'")
	lastChallengeCompleted = cur.fetchone()[0]

	if challengeID != None:
		lastChallengeCompleted += 1
		cur.execute(f"UPDATE coursesEnrolled SET lastChallengeCompleted = {lastChallengeCompleted}")
		conn.commit()

	cur.execute(f"SELECT challengeID FROM challenges WHERE courseID = '{courseID}' AND challengeNo={lastChallengeCompleted+1}")
	nextChallengeID = cur.fetchone()

	conn.close()

	if nextChallengeID == None:
		return jsonify("Finished")

	return jsonify(nextChallengeID[0])

@challenge_bp.route("/request_midi_notes_to_drum_name")
def request_midi_notes_to_drum_name():
	if not authenticate_token(request.headers):
		return "Invalid API key", 403

	midiNotesToDrumName = {
		35: "bass-drum",
		36: "bass-drum",
		37: "side-stick",
		38: "snare",
		40: "snare",
		41: "floor-tom",
		42: "closed hi-hat",
		43: "floor-tom",
		44: "pedal hi-hat",
		45: "mid-tom",
		46: "open hi-hat",
		47: "high-tom",
		49: "crash",
		51: "ride",
		53: "ride-bell",
		57: "crash"
	}

	return jsonify(midiNotesToDrumName)