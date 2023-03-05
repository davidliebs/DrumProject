from flask import Blueprint, jsonify, request
from models import returnDBConnection

import stripe
import json

payment_bp = Blueprint('payment_bp', __name__)

@payment_bp.route("/stripe-webhook", methods=["POST"])
def stripe_webhook():
	payload = request.get_data(as_text=True)
	sig_header = request.headers.get("Stripe-Signature")

	try:
		event = stripe.Webhook.construct_event(
			payload, sig_header, stripe_keys["endpoint_key"]
		)

	except ValueError as e:
		# Invalid payload
		return "Invalid payload", 400
	except stripe.error.SignatureVerificationError as e:
		# Invalid signature
		return "Invalid signature", 400

	# Handle the checkout.session.completed event
	if event["type"] == "checkout.session.completed":
		payload = json.loads(payload)
		userID = payload["data"]["object"]["client_reference_id"]

		conn, cur = returnDBConnection()

		cur.execute(f"""
			UPDATE users
			SET userPaid = 1
			WHERE userID = '{userID}'
		""")

		conn.commit()
		conn.close()

	return "Success", 200
