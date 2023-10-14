import logging
from typing import Any


from django.conf import settings
from django.db import models
from django.http import HttpRequest
from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField
from wagtail.models import Page

from paypal import paypal

logger = logging.getLogger(__name__)


class Subscription(models.Model):
    """A subscription to the magazine."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="subscriber",
        editable=True,
        on_delete=models.PROTECT,
        related_name="subscriptions",
    )

    paypal_subscription_id = models.CharField(
        max_length=255,
        null=False,
        blank=True,
        default="",
        unique=True,
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
    ]

    def __str__(self) -> str:
        return f"Subscription {self.id}"  # type: ignore

    @property
    def is_active(self) -> bool:
        """Return whether the subscription is active."""

        return paypal.subscription_is_active(
            paypal_subscription_id=self.paypal_subscription_id,
        )


class SubscriptionIndexPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
    ]

    parent_page_types = ["home.HomePage"]
    subpage_types: list[str] = []

    max_count = 1

    template = "subscription/index.html"


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

        if request.user.is_authenticated:
            subscriptions = Subscription.objects.filter(user=request.user)

            context["subscriptions"] = subscriptions

        return context
