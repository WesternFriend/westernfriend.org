from django.urls import reverse
from wagtail import blocks as wagtail_blocks


class PayPalSubscriptionPlanButtonBlock(wagtail_blocks.StructBlock):
    paypal_plan_id = wagtail_blocks.CharBlock(required=True)
    paypal_plan_name = wagtail_blocks.CharBlock(required=True)
    paypal_plan_price = wagtail_blocks.IntegerBlock(required=True)

    # Cache the URLs to avoid having to reverse them
    # for every block instance.
    _create_paypal_order_url: str = ""
    _manage_subscription_url: str = ""

    class Meta:
        icon = "link"
        template = "paypal/blocks/paypal_subscription_plan_button.html"

    def get_context(
        self,
        value,
        parent_context=None,
    ) -> str:
        """Return the URL to link a PayPal subscription to a user."""
        context = super().get_context(
            value,
            parent_context=parent_context,
        )

        context["link_paypal_subscription_url"] = reverse(
            "paypal:link_paypal_subscription",
        )

        return context
