from flask import Flask, render_template, jsonify, url_for, session

app = Flask(__name__)

@app.route("/user")
def home():
	return render_template("user/index.html")

@app.route("/user/challenge")
def challenge():
	return render_template("user/challenge.html")

app.run(port=8888, debug=True)