from flask import Flask, render_template, jsonify, send_from_directory, request
import json
import os
import uuid
import bcrypt
import mysql.connector
import stripe
import blob_storage_library
import process_challenge_files
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

stripe_keys = {
	"public_key": os.getenv("stripe_publishable_key"),
	"secret_key": os.getenv("stripe_secret_key"),
	"endpoint_key": os.getenv("stripe_webhook_secret_key")
}

stripe.api_key = stripe_keys["secret_key"]

b2_api, bucket = blob_storage_library.returnBucket()

beatbuddy_api_key = os.getenv("beatbuddy_api_key")

def returnDBConnection():
	conn = mysql.connector.connect(
		user = os.getenv("db_user"),
		password = os.getenv("db_password"),
		database = os.getenv("db_database"),
		host = os.getenv("db_host"),
		port = int(os.getenv("db_port"))
	)
	cur = conn.cursor()

	return conn, cur

def authenticate_token():
	if request.headers.get("Authorisation") == beatbuddy_api_key:
		return True
	
	return False

@app.route("/user/signup", methods=["POST"])
def user_signup():
	if not authenticate_token():
		return "Invalid API key", 403

	conn, cur = returnDBConnection()

	signup_data = request.json

	userID = str(uuid.uuid4())
	hashed_password = bcrypt.hashpw(signup_data["userPassword"].encode(), bcrypt.gensalt()).decode()

	cur.execute(f"""
		INSERT INTO users
		VALUES ('{userID}', '{signup_data["userEmail"]}', '{hashed_password}', 0)
	""")

	conn.commit()
	conn.close()

	return jsonify(userID)

@app.route("/user/login", methods=["POST"])
def user_login():
	if not authenticate_token():
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

@app.route("/user/get_paid_status", methods=["GET"])
def get_paid_status():
	if not authenticate_token():
		return "Invalid API key", 403

	conn, cur = returnDBConnection()

	userID = request.args.get("userID")

	cur.execute(f"""
		SELECT userPaid FROM users WHERE userID = '{userID}'
	""")

	userPaidStatus = cur.fetchone()[0]

	conn.close()

	return jsonify(userPaidStatus)

@app.route("/user/get_available_courses")
def get_available_courses():
	if not authenticate_token():
		return "Invalid API key", 403

	conn, cur = returnDBConnection()

	userID = request.args.get("userID")

	cur.execute(f"""
		SELECT * FROM courses WHERE courseID IN (SELECT courseID FROM coursesEnrolled WHERE userID = '{userID}');
	""")

	courses_enrolled = cur.fetchall()

	cur.execute(f"""
		SELECT * FROM courses WHERE courseID NOT IN (SELECT courseID FROM coursesEnrolled WHERE userID = '{userID}');
	""")

	other_courses = cur.fetchall()

	cur.execute(f"""
		SELECT coursesEnrolled.courseID, (coursesEnrolled.lastChallengeCompleted / courses.courseNoChallenges * 100)
		FROM coursesEnrolled
		INNER JOIN courses
		ON coursesEnrolled.userID='{userID}';
	""")

	user_progress = {i[0]: i[1] for i in cur.fetchall()}

	data_to_return = {
		"courses enrolled": courses_enrolled,
		"other courses": other_courses,
		"user progress": user_progress
	}

	conn.close()

	return jsonify(data_to_return)

@app.route("/user/request_music_notation_data")
def request_music_notation_data():
	if not authenticate_token():
		return "Invalid API key", 403

	conn, cur = returnDBConnection()

	courseID = request.args.get("courseID")
	challengeID = request.args.get("challengeID")

	cur.execute(f"SELECT musicData, svgIndexes, challengeTitle, challengeMessage, challengeSvgURL FROM challenges WHERE courseID = '{courseID}' AND challengeID = '{challengeID}'")
	music_notation_data = cur.fetchone()

	conn.close()

	return jsonify(music_notation_data)

@app.route("/user/get_next_challengeID")
def get_next_challenge_id():
	if not authenticate_token():
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

@app.route("/user/enroll_course")
def enroll_course():
	if not authenticate_token():
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

@app.route("/user/request_midi_notes_to_drum_name")
def request_midi_notes_to_drum_name():
	if not authenticate_token():
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

@app.route("/creator/create_course_entry", methods=["POST"])
def create_course_entry():
	if not authenticate_token():
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

	return course_id

@app.route("/creator/upload_course_logo", methods=["POST"])
def upload_course_logo():
	if not authenticate_token():
		return "Invalid API key", 403

	courseID = request.args.get("courseID")
	course_logo_file = request.files["course_logo"]

	course_logo_file.save(os.path.join(os.getenv("course_logo_upload_path"), courseID+".png"))

	return "Successful"

@app.route("/creator/create_challenge_entry", methods=["POST"])
def create_challenge_entry():
	if not authenticate_token():
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

	return challengeID

@app.route("/creator/process_challenge_svg_file", methods=["POST"])
def process_challenge_svg_file():
	if not authenticate_token():
		return "Invalid API key", 403

	conn, cur = returnDBConnection()

	svg_filepath = os.path.join(os.getenv("temporary_file_storage_path"), "challenge.svg")

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

@app.route("/creator/process_challenge_midi_file", methods=["POST"])
def process_challenge_midi_file():
	if not authenticate_token():
		return "Invalid API key", 403

	conn, cur = returnDBConnection()

	midi_filepath = os.path.join(os.getenv("temporary_file_storage_path"), "challenge.mid")

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

@app.route("/creator/fetch_courses", methods=["GET"])
def fetch_courses():
	if not authenticate_token():
		return "Invalid API key", 403

	conn, cur = returnDBConnection()

	cur.execute("SELECT courseID FROM courses")
	data = [i[0] for i in cur.fetchall()]

	conn.close()

	return jsonify(data)

@app.route("/creator/fetch_course_information", methods=["GET"])
def fetch_course_information():
	if not authenticate_token():
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

@app.route("/creator/delete_course", methods=["GET"])
def delete_course():
	if not authenticate_token():
		return "Invalid API key", 403

	conn, cur = returnDBConnection()

	courseID = request.args.get("courseID")

	cur.execute(f"DELETE FROM courses WHERE courseID='{courseID}'")
	cur.execute(f"DELETE FROM challenges WHERE courseID='{courseID}'")
	cur.execute(f"DELETE FROM coursesEnrolled WHERE courseID='{courseID}'")

	conn.commit()
	conn.close()

	return "Successful"

@app.route("/stripe-webhook", methods=["POST"])
def stripe_webhook():
	payload = request.get_data(as_text=True)
	sig_header = request.headers.get("Stripe-Signature")

	try:
		event = stripe.Webhook.construct_event(
			payload, sig_header, stripe_keys["endpoint_key"]
		)

	except ValueError as e:
		# Invalid payload
		return "Invalid payload", 400
	except stripe.error.SignatureVerificationError as e:
		# Invalid signature
		return "Invalid signature", 400

	# Handle the checkout.session.completed event
	if event["type"] == "checkout.session.completed":
		payload = json.loads(payload)
		userID = payload["data"]["object"]["client_reference_id"]

		conn, cur = returnDBConnection()

		cur.execute(f"""
			UPDATE users
			SET userPaid = 1
			WHERE userID = '{userID}'
		""")

		conn.commit()
		conn.close()

	return "Success", 200

app.run(port=5000, debug=True)