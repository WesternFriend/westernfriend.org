import os
import braintree


def get_braintree_gateway() -> braintree.BraintreeGateway:
    BRAINTREE_ENVIRONMENT = os.environ.get("BRAINTREE_ENVIRONMENT", "sandbox")
    braintree_env = (
        braintree.Environment.Production
        if BRAINTREE_ENVIRONMENT == "production"
        else braintree.Environment.Sandbox
    )

    braintree_gateway = braintree.BraintreeGateway(
        braintree.Configuration(
            braintree_env,
            merchant_id=os.environ.get("BRAINTREE_MERCHANT_ID"),
            public_key=os.environ.get("BRAINTREE_PUBLIC_KEY"),
            private_key=os.environ.get("BRAINTREE_PRIVATE_KEY"),
        ),
    )

    return braintree_gateway
