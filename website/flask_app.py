from flask import Flask, render_template, jsonify, url_for, session, Markup, request, send_from_directory, send_file
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

@app.route("/serve_challenge_svg")
def serve_challenge_svg():
	params = {"challengeId": request.args.get("challengeId")}
	res = requests.get("http://127.0.0.1:5000/serve_challenge_svg", params=params)

	file_obj = BytesIO(res.content)
	return send_file(file_obj, download_name="file.svg") 

app.run(port=8888, debug=True)