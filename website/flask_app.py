from flask import Flask, render_template, url_for, session, request, send_file, redirect
import requests
from io import BytesIO
import uuid

app = Flask(__name__)
app.secret_key = uuid.uuid4().hex

@app.route("/user/home")
def user_home():
	if not session.get("userID", False):
		return redirect("/user/login")

	session["challengeNo"] = 1

	return render_template("user/index.html")

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
	if not session.get("challengeNo", False):
		session["challengeNo"] = 1

	# fetching required data from api
	params = {"challengeId": "challenge"+str(session["challengeNo"])}
	res = requests.get("http://localhost:5000/user/request_music_notation_data", params=params)
	music_notation_data = res.json()

	res = requests.get("http://localhost:5000/user/request_midi_notes_to_drum_name")
	midi_notes_to_drum_name = res.json()

	return render_template("user/challenge.html", challengeId="challenge"+str(session["challengeNo"]), music_notation_data=music_notation_data, midi_notes_to_drum_name=midi_notes_to_drum_name)

@app.route("/user/fetch_challenge_svg")
def fetch_challenge_svg():
	params = {"challengeId": "challenge"+str(session["challengeNo"])}
	res = requests.get("http://127.0.0.1:5000/user/serve_challenge_svg", params=params)

	file_obj = BytesIO(res.content)
	return send_file(file_obj, download_name="file.svg")

@app.route("/user/next_challenge")
def next_challenge():
	if not session.get("challengeNo", False):
		session["challengeNo"] = 1
	else:
		session["challengeNo"] += 1

	return redirect("/user/challenge")

app.run(port=8888, debug=True)