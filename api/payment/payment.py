from flask import Blueprint, jsonify, request
from models import returnDBConnection, authenticate_token

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

		stripeSubscriptionID = payload["data"]["object"]["lines"]["data"][0]["subscription"]

		# getting user ID from metadata in subscription
		subscription_data = stripe.Subscription.retrieve(stripeSubscriptionID)
		userID = subscription_data["metadata"]["userID"]

		# if they have paid their invoice, create a record in the userPayment table
		# if they have renewed their subscription, a record should already exist so the code will update their subscription date

		renewal_date = (datetime.now()+timedelta(days=34)).strftime("%Y-%m-%d")

		conn, cur = returnDBConnection()

		cur.execute(f"""
			INSERT INTO userPayment(userID, subscriptionEnds, stripeSubscriptionID) VALUES ('{userID}', '{renewal_date}', '{stripeSubscriptionID}')
			ON DUPLICATE KEY
			UPDATE subscriptionEnds = '{renewal_date}', stripeSubscriptionID='{stripeSubscriptionID}'
		""")

		cur.execute(f"""
			UPDATE users
			SET userPaid = 1
			WHERE userID = '{userID}'
		""")

		conn.commit()
		conn.close()

	return "Success", 200

@payment_bp.route("/cancel_subscription", methods=["POST"])
def cancel_subscription():
	if not authenticate_token(request.headers):
		return "Invalid API key", 403

	conn, cur = returnDBConnection()
	
	userID = request.json["userID"]

	cur.execute(f"""
		SELECT stripeSubscriptionID FROM userPayment WHERE userID='{userID}'
	""")
	stripeSubscriptionID = cur.fetchone()[0]

	stripe.Subscription.delete(stripeSubscriptionID)

	return "Success"