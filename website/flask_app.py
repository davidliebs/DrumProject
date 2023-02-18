from flask import Flask, render_template, url_for, session, request, send_file, redirect
import requests
from io import BytesIO
import uuid
import json
import os
import stripe
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("app_secret_key")

@app.route("/")
def index():
	if session.get("userID", False):
		return redirect("/user/home")
	
	return redirect("/user/")

@app.route("/user/")
def user():
	if session.get("userID", False):
		return redirect("/user/home")

	return render_template("user/index.html")

@app.route("/user/home")
def user_home():
	if not session.get("userID", False):
		return redirect("/user/login")
	
	# fetching courses to display from api
	params = {"userID": session["userID"]}
	res = requests.get(f"{os.getenv('api_base_url')}/user/get_available_courses", params=params)
	courses = res.json()

	return render_template("user/home.html", courses=courses)

@app.route("/user/signup", methods=["GET", "POST"])
def user_signup():
	if request.method == "GET":
		return render_template("user/signup.html")
	
	user_email = request.form["userEmail"]
	user_pwd = request.form["userPassword"]

	data = {"userEmail": user_email, "userPassword": user_pwd}
	res = requests.post(f"{os.getenv('api_base_url')}/user/signup", json=data)

	return redirect("/user/login")

@app.route("/user/login", methods=["GET", "POST"])
def user_login():
	if request.method == "GET":
		return render_template("user/login.html")

	user_email = request.form["userEmail"]
	user_pwd = request.form["userPassword"]

	data = {"userEmail": user_email, "userPassword": user_pwd}
	res = requests.post(f"{os.getenv('api_base_url')}/user/login", json=data).json()

	if res == "Incorrect":
		return redirect("/user/login")

	session["userID"] = res
	
	return redirect("/user/home")

@app.route("/user/logout")
def user_logout():
	session.clear()

	return redirect("/user/")

@app.route("/user/challenge")
def challenge():
	if not session.get("userID", False):
		return redirect("/user/login")

	if session["challengeID"] == "Finished":
		return redirect("/user/home")

	# fetching required data from api
	params = {"courseID": session["courseID"], "challengeID": session["challengeID"]}
	res = requests.get(f"{os.getenv('api_base_url')}/user/request_music_notation_data", params=params)
	music_notation_data, svg_indexes, challengeTitle, challengeMessage, challengeSvgURL = res.json()

	res = requests.get(f"{os.getenv('api_base_url')}/user/request_midi_notes_to_drum_name", params={"userID": session["userID"]})
	midi_notes_to_drum_name = res.json()

	if midi_notes_to_drum_name == "no drum kits":
		return redirect("/user/calibrate")

	return render_template("user/challenge.html",
						   courseID=session["courseID"],
						   challengeID=session["challengeID"],
						   music_notation_data=music_notation_data,
						   midi_notes_to_drum_name=midi_notes_to_drum_name,
						   svg_indexes=svg_indexes,
						   challengeTitle=challengeTitle,
						   challengeMessage=challengeMessage,
						   challengeSvgURL=challengeSvgURL
	)

@app.route("/user/fetch_challenge_svg")
def fetch_challenge_svg():
	res = requests.get(request.args.get("challengeSvgURL"))

	file_obj = BytesIO(res.content)
	return send_file(file_obj, download_name="file.svg")

@app.route("/user/next_challenge")
def next_challenge():
	if not session.get("userID", False):
		return redirect("/user/login")

	courseID = request.args.get("courseID")
	challengeID = request.args.get("challengeID")

	session["courseID"] = courseID

	params = {"courseID": courseID, "challengeID": challengeID}
	res = requests.get(f"{os.getenv('api_base_url')}/user/get_next_challengeID", params=params)

	session["challengeID"] = res.json()

	return redirect("/user/challenge")

@app.route("/user/enroll-course")
def enroll_course():
	userID = session["userID"]
	courseID = request.args.get("courseID")

	params = {"userID": userID, "courseID": courseID}
	res = requests.get(f"{os.getenv('api_base_url')}/user/enroll_course", params=params)
	
	return redirect("/user/home")

@app.route("/user/calibrate", methods=["GET", "POST"])
def calibrate():
	if not session.get("userID", False):
		return redirect("/user/login")

	drums = [
				("snare", "snare", "snare"),
				("high tom", "high-tom", "high-tom"),
				("mid tom", "mid-tom", "mid-tom"),
				("floor tom", "floor-tom", "floor-tom"),
				("bass drum", "bass-drum", "bass-drum"),
				("hi-hat (closed)", "hh-closed", "closed hi-hat"),
				("hi-hat(open)", "hh-open", "open hi-hat"),
				("crash (1)", "crash-1", "crash"),
				("crash (2)", "crash-2", "crash"),
				("ride", "ride", "ride")
	]

	if request.method == "GET":	
		res = requests.get(f"{os.getenv('api_base_url')}/user/request_midi_notes_to_drum_name", params={"userID": session["userID"]})
		midi_notes_to_drum_name = res.json()

		drum_kit_exists=True
		if midi_notes_to_drum_name == "no drum kits":
			drum_kit_exists=False
		
		return render_template("user/calibrate.html", drums=drums, drum_kit_exists=drum_kit_exists)

	if request.method == "POST":
		drum_kit_data = {}

		for i in drums:
			drum_kit_data[int(request.form[i[1]])] = i[2]
		
		data = {"userID": session["userID"], "drumKitData": drum_kit_data}
		res = requests.post(f"{os.getenv('api_base_url')}/user/calibrate_drum_kit", json=data)

		return redirect("/user/home")

app.run(host="0.0.0.0", port=8888, debug=True)