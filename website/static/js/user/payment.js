let stripe;

fetch("/user/payment/config")
	.then((result) => { return result.json(); })
	.then((data) => {
		// Initialize Stripe.js
		stripe = Stripe(data.public_key);
	});

$(document).ready(function() {
	$("#continuePaymentButton").click(function() {
		fetch("/user/payment/create-checkout-session")
		.then((result) => { return result.json(); })
		.then((data) => {
			console.log(data);
			// Redirect to Stripe Checkout
			return stripe.redirectToCheckout({sessionId: data.sessionId})
		})
		.then((res) => {
			console.log(res);
		});
	});
});