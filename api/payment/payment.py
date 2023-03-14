from flask import Blueprint, jsonify, request
from models import returnDBConnection

import os
from dotenv import load_dotenv
import stripe
import json
from datetime import datetime, timedelta

load_dotenv()

payment_bp = Blueprint('payment_bp', __name__)

stripe.api_key = os.getenv("stripe_secret_key")

@payment_bp.route("/stripe-webhook", methods=["POST"])
def stripe_webhook():
	payload = request.get_data(as_text=True)
	sig_header = request.headers.get("Stripe-Signature")

	try:
		event = stripe.Webhook.construct_event(
			payload, sig_header, os.getenv("stripe_webhook_secret_key")
		)

	except ValueError as e:
		# Invalid payload
		return "Invalid payload", 400
	except stripe.error.SignatureVerificationError as e:
		# Invalid signature
		return "Invalid signature", 400

	# Handle the checkout.session.completed event
	if event["type"] == "invoice.paid":
		payload = json.loads(payload)

		conn, cur = returnDBConnection()

		# getting user ID
		subscription_data = stripe.Subscription.retrieve(payload["data"]["object"]["lines"]["data"][0]["subscription"])
		userID = subscription_data["metadata"]["userID"]

		# if they have paid their invoice, create a record in the userPayment table
		# if they have renewed their subscription, a record should already exist so the code will update their subscription date

		renewal_date = (datetime.now()+timedelta(days=34)).strftime("%Y-%m-%d")

		cur.execute(f"""
			INSERT INTO userPayment(userID, subscriptionEnds) VALUES ('{userID}', '{renewal_date}')
			ON DUPLICATE KEY
			UPDATE subscriptionEnds = '{renewal_date}'
		""")

		cur.execute(f"""
			UPDATE users
			SET userPaid = 1
			WHERE userID = '{userID}'
		""")

		conn.commit()
		conn.close()

	return "Success", 200
