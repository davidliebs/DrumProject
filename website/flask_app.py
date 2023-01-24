from flask import Flask, render_template, jsonify, url_for

app = Flask(__name__)

@app.route("/")
def home():
	return render_template("index.html")

app.run(port=8888, debug=True)