from flask import Flask, render_template, url_for, session, request, send_file, redirect
import requests
from io import BytesIO
import uuid
import json

app = Flask(__name__)
app.secret_key = uuid.uuid4().hex

@app.route("/user/home")
def user_home():
	if not session.get("userID", False):
		return redirect("/user/login")
	
	# fetching courses to display from api
	params = {"userID": session["userID"]}
	res = requests.get("http://localhost:5000/user/get_available_courses", params=params)
	courses = res.json()

	return render_template("user/home.html", courses=courses)

@app.route("/user/signup", methods=["GET", "POST"])
def user_signup():
	if request.method == "GET":
		return render_template("user/signup.html")
	
	user_email = request.form["userEmail"]
	user_pwd = request.form["userPassword"]

	data = {"userEmail": user_email, "userPassword": user_pwd}
	res = requests.post("http://localhost:5000/user/signup", json=data)

	return redirect("/user/login")

@app.route("/user/login", methods=["GET", "POST"])
def user_login():
	if request.method == "GET":
		return render_template("user/login.html")

	user_email = request.form["userEmail"]
	user_pwd = request.form["userPassword"]

	data = {"userEmail": user_email, "userPassword": user_pwd}
	res = requests.post("http://localhost:5000/user/login", json=data).json()

	if res == "Incorrect":
		return redirect("/user/login")

	session["userID"] = res
	
	return redirect("/user/home")

@app.route("/user/challenge")
def challenge():
	if session["challengeID"] == "Finished":
		return redirect("/user/home")

	# fetching required data from api
	params = {"courseID": session["courseID"], "challengeID": session["challengeID"]}
	res = requests.get("http://localhost:5000/user/request_music_notation_data", params=params)
	music_notation_data, svg_indexes = res.json()

	res = requests.get("http://localhost:5000/user/request_midi_notes_to_drum_name")
	midi_notes_to_drum_name = res.json()

	return render_template("user/challenge.html", courseID=session["courseID"], challengeID=session["challengeID"], music_notation_data=music_notation_data, midi_notes_to_drum_name=midi_notes_to_drum_name, svg_indexes=svg_indexes)

@app.route("/user/fetch_challenge_svg")
def fetch_challenge_svg():
	params = {"courseID": session["courseID"], "challengeID": session["challengeID"]}
	res = requests.get("http://127.0.0.1:5000/user/serve_challenge_svg", params=params)

	file_obj = BytesIO(res.content)
	return send_file(file_obj, download_name="file.svg")

@app.route("/user/next_challenge")
def next_challenge():
	courseID = request.args.get("courseID")
	challengeID = request.args.get("challengeID")

	session["courseID"] = courseID

	params = {"courseID": courseID, "challengeID": challengeID}
	res = requests.get("http://127.0.0.1:5000/user/get_next_challengeID", params=params)

	session["challengeID"] = res.json()

	return redirect("/user/challenge")

@app.route("/user/enroll-course")
def enroll_course():
	userID = session["userID"]
	courseID = request.args.get("courseID")

	params = {"userID": userID, "courseID": courseID}
	res = requests.get("http://127.0.0.1:5000/user/enroll_course", params=params)
	
	return redirect("/user/home")

app.run(port=8888, debug=True)