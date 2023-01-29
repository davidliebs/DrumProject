from flask import Flask, render_template, url_for, session, request, send_file, redirect
import requests
from io import BytesIO
import uuid

app = Flask(__name__)
app.secret_key = uuid.uuid4().hex

@app.route("/user")
def user_home():
	session["challengeNo"] = 1
	return render_template("user/index.html")

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