from flask import Flask, render_template, url_for, session, request, send_file, redirect, jsonify
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

stripe_keys = {
	"public_key": os.getenv("stripe_publishable_key"),
	"secret_key": os.getenv("stripe_secret_key")
}

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
	
	message = ""
	if request.args.get("limit_message", False):
		message = "The number of courses you have enrolled to has reached its limit, upgrade your plan so you can enroll to more"

	# fetching user paid status
	params = {"userID": session["userID"]}

	res = requests.get(f"{os.getenv('api_base_url')}/user/get_paid_status", params=params)
	session["userPaid"] = res.json()
	
	# fetching courses to display from api
	res = requests.get(f"{os.getenv('api_base_url')}/user/get_available_courses", params=params)
	courses = res.json()

	return render_template("user/home.html", courses=courses, userPaid=session["userPaid"], message=message)

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

	session["userID"] = res["userID"]

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

	params = {"userID": userID, "courseID": courseID, "userPaid": session["userPaid"]}
	res = requests.get(f"{os.getenv('api_base_url')}/user/enroll_course", params=params)

	if res.json() == "Limit reached":
		return redirect("/user/home?limit_message=1")
	
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

@app.route("/user/payment")
def payment():
	if not session.get("userID", False):
		return redirect("/user/login")
	
	return render_template("user/payment.html")

@app.route("/user/payment/config")
def payment_config():
	return jsonify({"public_key": stripe_keys["public_key"]})

@app.route("/user/payment/create-checkout-session")
def create_checkout_session():
	if not session.get("userID", False):
		return redirect("/user/login")

	domain_url = os.getenv("domain_url")
	stripe.api_key = stripe_keys["secret_key"]

	try:
		checkout_session = stripe.checkout.Session.create(
			success_url=domain_url + "user/payment/success?session_id={CHECKOUT_SESSION_ID}",
			cancel_url=domain_url,
			payment_method_types=["card"],
			mode="subscription",
			line_items=[
				{
					"price": "price_1McoKrIe9NIvPil7UyC1v8ed",
					"quantity": 1
				}
			],
			client_reference_id=session["userID"]
		)
		return jsonify({"sessionId": checkout_session["id"]})

	except Exception as e:
		return jsonify(error=str(e))

@app.route("/user/payment/success")
def payment_success():
	return render_template("user/payment-success.html")

app.run(port=8888, debug=True)