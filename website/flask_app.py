from flask import Flask, render_template, url_for, session, request, send_file
import requests
from io import BytesIO

app = Flask(__name__)

@app.route("/user")
def home():
	return render_template("user/index.html")

@app.route("/user/challenge")
def challenge():
	challengeId = "challenge1"

	return render_template("user/challenge.html", challengeId=challengeId)

@app.route("/fetch_challenge_svg")
def fetch_challenge_svg():
	params = {"challengeId": request.args.get("challengeId")}
	res = requests.get("http://127.0.0.1:5000/serve_challenge_svg", params=params)

	file_obj = BytesIO(res.content)
	return send_file(file_obj, download_name="file.svg")

@app.route("/user/next_challenge")
def next_challenge():
	return "hello"

app.run(port=8888, debug=True)