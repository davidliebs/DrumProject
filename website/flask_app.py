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
	"secret_key": os.getenv("stripe_secret_key"),
	"price_id": os.getenv("price_id")
}

beat_buddy_api_headers = {"Authorisation": os.getenv("beatbuddy_api_key")}

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
	
	session["courseID"] = None
	session["challengeID"] = None

	message = ""
	if request.args.get("limit_message", False):
		message = "The number of courses you have enrolled to has reached its limit, upgrade your plan so you can enroll to more"

	# fetching user details
	params = {"userID": session["userID"]}

	res = requests.get(f"{os.getenv('api_base_url')}/userInfo/get_user_details", params=params, headers=beat_buddy_api_headers)
	user_details = res.json()

	session["userPaid"] = user_details[0]
	session["userEmailVerified"] = user_details[1]
	session["userEmail"] = user_details[2]
	
	# fetching courses to display from api
	res = requests.get(f"{os.getenv('api_base_url')}/userInfo/get_available_courses", params=params, headers=beat_buddy_api_headers)
	courses = res.json()

	return render_template("user/home.html", courses=courses, userPaid=session["userPaid"], message=message, userEmailVerified=session["userEmailVerified"])

@app.route("/user/signup", methods=["GET", "POST"])
def user_signup():
	if request.method == "GET":
		return render_template("user/signup.html")
	
	user_email = request.form["userEmail"]
	user_pwd = request.form["userPassword"]

	data = {"userEmail": user_email, "userPassword": user_pwd}
	res = requests.post(f"{os.getenv('api_base_url')}/userAuth/signup", json=data, headers=beat_buddy_api_headers)

	return redirect("/user/login")

@app.route("/user/send_verification_email", methods=["GET"])
def send_verification_email():
	if not session.get("userID", False):
		return redirect("/user/login")

	res = requests.get(f"{os.getenv('api_base_url')}/emailHandler/send_verification_email", params={"userID": session["userID"]}, headers=beat_buddy_api_headers)
	response = res.json()

	return redirect("/user/home")

@app.route("/user/verify_email", methods=["GET"])
def verify_email():
	token = request.args.get("token")

	res = requests.get(f"{os.getenv('api_base_url')}/userAuth/verify_email", params={"token": token}, headers=beat_buddy_api_headers)
	response = res.json()

	return render_template("user/verify_email.html", response=response)

@app.route("/user/login", methods=["GET", "POST"])
def user_login():
	if request.method == "GET":
		return render_template("user/login.html")

	user_email = request.form["userEmail"]
	user_pwd = request.form["userPassword"]

	data = {"userEmail": user_email, "userPassword": user_pwd}
	res = requests.post(f"{os.getenv('api_base_url')}/userAuth/login", json=data, headers=beat_buddy_api_headers).json()

	if res == "Incorrect":
		return redirect("/user/login")

	session["userID"] = res["userID"]
	session["userAdmin"] = res["userAdmin"]

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
	res = requests.get(f"{os.getenv('api_base_url')}/challenge/request_music_notation_data", params=params, headers=beat_buddy_api_headers)
	music_notation_data, svg_indexes, challengeTitle, challengeMessage, challengeSvgURL = res.json()

	res = requests.get(f"{os.getenv('api_base_url')}/challenge/request_midi_notes_to_drum_name", params={"userID": session["userID"]}, headers=beat_buddy_api_headers)
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
	res = requests.get(request.args.get("challengeSvgURL"), headers=beat_buddy_api_headers)

	file_obj = BytesIO(res.content)
	return send_file(file_obj, download_name="file.svg")

@app.route("/user/next_challenge")
def next_challenge():
	if not session.get("userID", False):
		return redirect("/user/login")

	courseID = request.args.get("courseID")
	challengeID = request.args.get("challengeID")

	session["courseID"] = courseID

	params = {"userID": session["userID"], "courseID": courseID, "challengeID": challengeID}
	res = requests.get(f"{os.getenv('api_base_url')}/challenge/get_next_challengeID", params=params, headers=beat_buddy_api_headers)

	session["challengeID"] = res.json()

	return redirect("/user/challenge")

@app.route("/user/enroll-course")
def enroll_course():
	userID = session["userID"]
	courseID = request.args.get("courseID")

	params = {"userID": userID, "courseID": courseID, "userPaid": session["userPaid"]}
	res = requests.get(f"{os.getenv('api_base_url')}/course/enroll_course", params=params, headers=beat_buddy_api_headers)

	if res.json() == "Limit reached":
		return redirect("/user/home?limit_message=1")
	
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
					"price": stripe_keys["price_id"],
					"quantity": 1,
				}
			],
			subscription_data = {
				"metadata": {
					"userID": session["userID"]
				}
			}
		)
		return jsonify({"sessionId": checkout_session["id"]})

	except Exception as e:
		return jsonify(error=str(e))

@app.route("/user/payment/success")
def payment_success():
	if not session.get("userID", False):
		return redirect("/user/login")

	return render_template("user/payment-success.html")

@app.route("/user/cancel_subscription")
def cancel_subscription():
	if not session.get("userID", False):
		return redirect("/user/login")
	
	data = {"userID": session["userID"]}
	requests.post(f"{os.getenv('api_base_url')}/payment/cancel_subscription", json=data, headers=beat_buddy_api_headers)

	return redirect("/user/account")

@app.route("/user/account", methods=["GET"])
def user_account():
	if not session.get("userID", False):
		return redirect("/user/login")

	# fetching user details
	params = {"userID": session["userID"]}

	res = requests.get(f"{os.getenv('api_base_url')}/userInfo/get_user_details", params=params, headers=beat_buddy_api_headers)
	user_details = res.json()

	return render_template("user/account.html", userPaid=user_details[0], userEmailVerified=user_details[1], userEmail=user_details[2])

@app.route("/user/change-email", methods=["POST"])
def user_change_email():
	if not session.get("userID", False):
		return redirect("/user/login")

	# ping api endpoint to change email
	params = {"userID": session["userID"], "newEmail": request.form.get("newEmail")}
	requests.get(f"{os.getenv('api_base_url')}/userAuth/change_email", params=params, headers=beat_buddy_api_headers)

	# ping api endpoint to send email verification
	requests.get(f"{os.getenv('api_base_url')}/email/send_verification_email", params={"userID": session["userID"]}, headers=beat_buddy_api_headers)

	return redirect("/user/account")

@app.route("/user/change-password", methods=["POST"])
def change_password():
	if not session.get("userID", False):
		return redirect("/user/login")

	currentPassword = request.form.get("currentPassword")
	newPassword = request.form.get("newPassword")

	# using api login endpoint to verify password from user == to their current password
	data = {"userEmail": session["userEmail"], "userPassword": currentPassword}
	res = requests.post(f"{os.getenv('api_base_url')}/userAuth/login", json=data, headers=beat_buddy_api_headers).json()

	if res == "Incorrect":
		return redirect("/user/account")

	# updating their password
	data = {"userID": session["userID"], "newPassword": newPassword}
	requests.post(f"{os.getenv('api_base_url')}/userAuth/change_password", json=data, headers=beat_buddy_api_headers)

	return redirect("/user/logout")

@app.route("/user/delete-account", methods=["POST"])
def delete_account():
	if not session.get("userID", False):
		return redirect("/user/login")

	requests.get(f"{os.getenv('api_base_url')}/userAuth/delete_account", params={"userID": session["userID"]}, headers=beat_buddy_api_headers)

	return redirect("/user/logout")

@app.route("/user/forgot-password", methods=["GET", "POST"])
def forgot_password():
	if request.method == "GET":
		message = ""
		if request.args.get("message") == "1":
			message = "That email isn't in our database"
		elif request.args.get("message") == "2":
			message = "The link sent to your email has expired"
		elif request.args.get("message") == "3":
			message = "An email has been sent to you to reset your password"

		return render_template("user/forgot_password.html", message=message)
	
	if request.method == "POST":
		userEmail = request.form.get("userEmail")

		# check their email exists	
		payload = {"userEmail": userEmail}
		res = requests.post(f"{os.getenv('api_base_url')}/userAuth/check_email_exists", json=payload, headers=beat_buddy_api_headers)

		data = res.json()

		if data == False:
			return redirect("/user/forgot-password?message=1")
		
		userID = data.get("userID")
		session["userID"] = userID

		# send email with link to reset their password
		payload = {"userID": userID, "userEmail": userEmail}
		requests.post(f"{os.getenv('api_base_url')}/emailHandler/send_forgot_password_email", json=payload, headers=beat_buddy_api_headers)

		return redirect("/user/forgot-password?message=3")

@app.route("/user/reset-password", methods=["GET", "POST"])
def reset_password():
	if not session.get("userID", False):
		return redirect("/user/login")

	if request.method == "GET":
		return render_template("user/reset_password.html", token=request.args.get("token"))
	
	newPassword = request.form.get("newPassword")
	token = request.form.get("token")

	# verifying token is valid
	data = {"userID": session["userID"], "token": token}
	res = requests.post(f"{os.getenv('api_base_url')}/userAuth/verify_reset_password_token", json=data, headers=beat_buddy_api_headers)

	if res.json() == False:
		return redirect("/user/forgot-password?message=2")

	# sending request to reset password
	data = {"userID": session["userID"], "newPassword": newPassword}
	requests.post(f"{os.getenv('api_base_url')}/userAuth/change_password", json=data, headers=beat_buddy_api_headers)

	return redirect("/user/logout")

@app.route("/user/subscribe-to-newsletter", methods=["POST"])
def subscribe_to_newsletter():
	emailToAdd = request.form.get("email")

	data = {"email": emailToAdd, "subscribe": "yes"}
	requests.post(f"{os.getenv('api_base_url')}/userInfo/subscribe_to_newsletter", json=data, headers=beat_buddy_api_headers)

	return redirect("/")

@app.route("/user/unsubscribe-from-newsletter", methods=["GET", "POST"])
def unsubscribe_from_newsletter():
	if request.method == "GET":
		return render_template("user/newsletter_unsubscription.html")

	emailToRemove = request.form.get("email")

	data = {"email": emailToRemove, "subscribe": "no"}
	requests.post(f"{os.getenv('api_base_url')}/userInfo/subscribe_to_newsletter", json=data, headers=beat_buddy_api_headers)

	return redirect("/")

@app.route("/user/terms-and-conditions", methods=["GET"])
def terms_and_conditions():
	return render_template("user/terms_and_conditions.html")

@app.route("/creator/home")
def creator_home():
	if not session.get("userID", False) or session.get("userAdmin", False) != 1:
		return redirect("/user/login")

	# fetching courses
	res = requests.get(f"{os.getenv('api_base_url')}/creator/fetch_courses", headers=beat_buddy_api_headers)
	courses = res.json()

	return render_template("creator/home.html", courses=courses)

@app.route("/creator/add_course", methods=["GET", "POST"])
def add_course():
	if not session.get("userID", False) or session.get("userAdmin", False) != 1:
		return redirect("/user/login")

	if request.method == "GET":
		return render_template("creator/add_course.html")

	courseName = request.form.get("courseName")
	courseDescription = request.form.get("courseDescription")
	courseNoChallenges = request.form.get("courseNoChallenges")
	courseLogoFile = request.files.get("courseLogo")

	# create course entry
	data = {
		"courseName": courseName,
		"courseDescription": courseDescription,
		"courseNoChallenges": courseNoChallenges
	}

	res = requests.post(f"{os.getenv('api_base_url')}/creator/create_course_entry", json=data, headers=beat_buddy_api_headers)
	courseID = res.text

	files=[
		('course_logo', ('course-logo.png', courseLogoFile.read(),'image/png'))
	]

	requests.post(f"{os.getenv('api_base_url')}/creator/upload_course_logo", params={"courseID": courseID}, files=files, headers=beat_buddy_api_headers)
	
	return redirect("/creator/home")

@app.route("/creator/edit_course", methods=["GET"])
def edit_course():
	if not session.get("userID", False) or session.get("userAdmin", False) != 1:
		return redirect("/user/login")

	courseID = request.args.get("courseID")

	res = requests.get(f"{os.getenv('api_base_url')}/creator/fetch_course_information", params={"courseID": courseID}, headers=beat_buddy_api_headers)
	data = res.json()

	return render_template("creator/edit_course.html", data=data)

@app.route("/creator/edit_course_information", methods=["POST"])
def edit_course_information():
	if not session.get("userID", False) or session.get("userAdmin", False) != 1:
		return redirect("/user/login")

	courseID = request.form.get("courseID")

	courseName = request.form.get("courseName")
	courseDescription = request.form.get("courseDescription")
	courseNoChallenges = request.form.get("courseNoChallenges")
	courseLogoFile = request.files.get("courseLogo")

	if courseLogoFile.filename != '':
		params={"courseID": courseID}
		files=[
			('course_logo', ('course-logo.png', courseLogoFile.read(),'image/png'))
		]

		requests.post(f"{os.getenv('api_base_url')}/creator/upload_course_logo", params=params, files=files, headers=beat_buddy_api_headers)
	
	data = {"courseID": courseID, "courseName": courseName, "courseDescription": courseDescription, "courseNoChallenges": courseNoChallenges}
	requests.post(f"{os.getenv('api_base_url')}/creator/create_course_entry", json=data, headers=beat_buddy_api_headers)

	return redirect("/creator/home")

@app.route("/creator/edit_challenge_information", methods=["POST"])
def edit_challenge_information():
	if not session.get("userID", False) or session.get("userAdmin", False) != 1:
		return redirect("/user/login")

	challengeID = request.form.get("challengeID")
	courseID = request.form.get("courseID")

	challengeNo = request.form.get("challengeNo")
	challengeTitle = request.form.get("challengeTitle")
	challengeMessage = request.form.get("challengeMessage")
	challengeSVGFile = request.files.get("challengeSVGFile")
	challengeMIDIFile = request.files.get("challengeMIDIFile")

	data = {
		"courseID": courseID,
		"challengeNo": challengeNo,
		"challengeTitle": challengeTitle,
		"challengeMessage": challengeMessage
	}

	if challengeID != None:
		data["challengeID"] = challengeID

	res = requests.post(f"{os.getenv('api_base_url')}/creator/create_challenge_entry", json=data, headers=beat_buddy_api_headers)
	challengeID = res.text

	if challengeSVGFile.filename != '':
		params = {"challengeID": challengeID}
		files=[
			('challengeSVGFile',('challenge_svg.svg', challengeSVGFile.read(),'image/svg+xml'))
		]
		requests.post(f"{os.getenv('api_base_url')}/creator/process_challenge_svg_file", files=files, params=params, headers=beat_buddy_api_headers)

	if challengeMIDIFile.filename != '':
		params = {"challengeID": challengeID}
		files=[
			('challengeMIDIFile',('challenge_midi.mid', challengeMIDIFile.read(),'audip/midi'))
		]
		requests.post(f"{os.getenv('api_base_url')}/creator/process_challenge_midi_file", files=files, params=params, headers=beat_buddy_api_headers)

	return redirect("/creator/home")

@app.route("/creator/delete_course", methods=["GET"])
def delete_course():
	if not session.get("userID", False) or session.get("userAdmin", False) != 1:
		return redirect("/user/login")

	courseID = request.args.get("courseID")

	requests.get(f"{os.getenv('api_base_url')}/creator/delete_course", params={"courseID": courseID}, headers=beat_buddy_api_headers)

	return redirect("/creator/home")

app.run(port=8888, debug=True)