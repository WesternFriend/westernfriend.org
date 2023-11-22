import logging
from typing import Any
from django.shortcuts import redirect

from django.utils import timezone
from django.conf import settings
from django.db import models
from django.http import HttpRequest, HttpResponse
from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField, StreamField
from wagtail import blocks as wagtail_blocks
from wagtail.models import Page

from paypal import blocks as paypal_blocks

from paypal import subscriptions as paypal_subscriptions

logger = logging.getLogger(__name__)


class Subscription(models.Model):
    """A subscription to the magazine."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        verbose_name="subscriber",
        editable=True,
        on_delete=models.PROTECT,
        related_name="subscription",
        unique=True,  # Only one subscription per user
    )

    paypal_subscription_id = models.CharField(
        help_text="The PayPal subscription ID. If this field has a value, PayPal will manage the expiration date.",
        max_length=255,
        null=True,
        blank=True,
        unique=True,
    )

    expiration_date = models.DateField(
        help_text="The date the subscription expires. Leave blank for perpetual subscriptions.",
        null=True,
        blank=True,
    )

    class Meta:
        indexes = [
            models.Index(
                fields=["paypal_subscription_id"],
            ),
        ]

    panels = [
        FieldPanel("user"),
        FieldPanel(
            "paypal_subscription_id",
            read_only=True,
        ),
        FieldPanel("expiration_date"),
    ]

    def __str__(self) -> str:
        return f"Subscription {self.id}"  # type: ignore

    @property
    def is_active(self) -> bool:
        """Return whether the subscription is active.

        If the subscription has a PayPal subscription ID, check with
        PayPal.

        Otherwise, if the subscription has an expiration date, check
        that the date is in the future.

        Otherwise, the subscription is perpetually active (e.g., a Board
        member subscription).
        """

        if self.paypal_subscription_id:
            return paypal_subscriptions.subscription_is_active(
                paypal_subscription_id=self.paypal_subscription_id,
            )

        if self.expiration_date is not None:
            expires_in_future = self.expiration_date >= timezone.now().date()
            return expires_in_future

        # Default to inactive for safety
        return False


class SubscriptionIndexPage(Page):
    intro = RichTextField(blank=True)

    body = StreamField(
        [
            (
                "paragraph",
                wagtail_blocks.RichTextBlock(),
            ),
            (
                "paypal_card_row",
                wagtail_blocks.ListBlock(
                    paypal_blocks.PayPalSubscriptionPlanButtonBlock(),
                    template="blocks/blocks/card_row.html",
                ),
            ),
        ],
        blank=True,
        use_json_field=True,
    )

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        FieldPanel("body"),
    ]

    parent_page_types = ["home.HomePage"]
    subpage_types: list[str] = []

    max_count = 1

    template = "subscription/index.html"

    def get_context(
        self,
        request: HttpRequest,
        *args: tuple,
        **kwargs: dict,
    ) -> dict[str, Any]:
        context = super().get_context(request)

        context["paypal_client_id"] = settings.PAYPAL_CLIENT_ID  # type: ignore

        return context

    def serve(
        self,
        request: HttpRequest,
        *args: tuple,
        **kwargs: dict,
    ) -> HttpResponse:
        # Redirect to the Manage Subscription page
        # if the user is logged in and has a subscription.
        if (
            hasattr(request, "user")
            and request.user.is_authenticated
            and request.user.is_subscriber
        ):
            # redirect to manage subscription page
            manage_subscription_page = ManageSubscriptionPage.objects.first()

            if manage_subscription_page:
                return redirect(
                    manage_subscription_page.url,
                )

        return super().serve(request, *args, **kwargs)


class ManageSubscriptionPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
    ]

    parent_page_types = ["home.HomePage"]
    subpage_types: list[str] = []

    max_count = 1

    def get_context(
        self,
        request: HttpRequest,
        *args: tuple,
        **kwargs: dict,
    ) -> dict[str, Any]:
        context = super().get_context(request)

        if (
            hasattr(request, "user")
            and request.user.is_authenticated
            and hasattr(request.user, "subscription")
        ):
            context["subscription"] = request.user.subscription

        return context
