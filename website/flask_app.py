from flask import Flask, render_template, url_for, session, request, send_file, redirect
import requests
from io import BytesIO
import uuid

app = Flask(__name__)
app.secret_key = uuid.uuid4().hex

@app.route("/user")
def home():
	session["challengeNo"] = 1
	return render_template("user/index.html")

@app.route("/user/challenge")
def challenge():
	if not session.get("challengeNo", False):
		session["challengeNo"] = 1

	return render_template("user/challenge.html", challengeId="challenge"+str(session["challengeNo"]))

@app.route("/user/fetch_challenge_svg")
def fetch_challenge_svg():
	params = {"challengeId": "challenge"+str(session["challengeNo"])}
	res = requests.get("http://127.0.0.1:5000/serve_challenge_svg", params=params)

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