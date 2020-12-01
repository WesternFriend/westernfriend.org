import datetime
import logging
import os

import braintree

from django.conf import settings
from django.contrib.auth import login
from django.db import models
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse

from wagtail.admin.edit_handlers import FieldPanel
from wagtail.core.fields import RichTextField
from wagtail.core.models import Page


from flatpickr import DatePickerInput

logger = logging.getLogger(__name__)


MAGAZINE_FORMAT_CHOICES = [
    ("pdf", "PDF"),
    ("print", "Print"),
    ("print_and_pdf", "Print and PDF"),
]

MAGAZINE_PRICE_GROUP_CHOICES = [
    ("normal", "Normal"),
    ("true_cost", "True cost"),
    ("low_income", "Low income"),
    ("international", "International"),
]

SUBSCRIPTION_PRICE_COMPONENTS = {
    "normal": {
        "pdf": 30,
        "print": 36,
        "print_and_pdf": 48,
    },
    "true_cost": {
        "pdf": 60,
        "print": 72,
        "print_and_pdf": 96,
    },
    "low_income": {
        "pdf": 20,
        "print": 20,
        "print_and_pdf": 25,
    },
    "international": {
        "pdf": 30,
        "print": 55,
        "print_and_pdf": 70,
    },
}


def process_subscription_form(subscription_form, request):
    """
    Given a valid subscription form, will save and associate with a user.

    TODO: determine how to share this function with the "manage subscription" page
    """
    # Create a temporary subscription object to modify it's fields
    subscription = subscription_form.save(commit=False)

    # Attach request user to subscription before save
    subscription.user = request.user

    # Set subscription start and end dates
    # based on current day
    today = datetime.datetime.now()

    # Start date is today
    subscription.start_date = today

    # End date is today
    # until we get a success message from the payment processor
    subscription.end_date = today

    subscription.save()

    # set the order in the session
    request.session["subscription_id"] = subscription.id

    # redirect for payment
    return redirect(
        reverse("payment:process", kwargs={"previous_page": "subscribe"})
    )


class Subscription(models.Model):
    format = models.CharField(max_length=255, choices=MAGAZINE_FORMAT_CHOICES, default="pdf")
    price_group = models.CharField(max_length=255, choices=MAGAZINE_PRICE_GROUP_CHOICES, default="normal")
    price = models.IntegerField(editable=False)
    recurring = models.BooleanField(default=True)
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)
    subscriber_given_name = models.CharField(
        max_length=255,
        default="",
        help_text="Enter the given (first) name for the subscriber.",
    )
    subscriber_family_name = models.CharField(
        max_length=255,
        default="",
        help_text="Enter the family (last) name for the subscriber.",
    )
    subscriber_street_address = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="The street address where a print subscription could be mailed.",
    )
    subscriber_street_address_line_2 = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="If needed, second line for mailing address.",
    )
    subscriber_postal_code = models.CharField(
        max_length=16, help_text="Postal code for the mailing address.", blank=True,
    )
    subscriber_address_locality = models.CharField(
        max_length=255, help_text="City for the mailing address.", blank=True,
    )
    subscriber_address_region = models.CharField(
        max_length=255,
        help_text="State for the mailing address.",
        blank=True,
        default="",
    )
    subscriber_address_country = models.CharField(
        max_length=255,
        default="United States",
        help_text="Country for mailing.",
        blank=True,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="subscriber email",
        # TODO: determine whether we want these to be nullable
        # e.g. for tracking subscriptions created offline
        # null=True,
        # blank=True,
        editable=True,
        on_delete=models.PROTECT,
        related_name="subscriptions",
    )

    paid = models.BooleanField(default=False)

    braintree_subscription_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="DO NOT EDIT. Used to cross-reference subscriptions with Braintree payments.",
    )

    panels = [
        FieldPanel("user"),
        FieldPanel("subscriber_given_name"),
        FieldPanel("subscriber_family_name"),
        FieldPanel("subscriber_street_address"),
        FieldPanel("subscriber_street_address_line_2"),
        FieldPanel("subscriber_postal_code"),
        FieldPanel("subscriber_address_locality"),
        FieldPanel("subscriber_address_region"),
        FieldPanel("subscriber_address_country"),
        FieldPanel("start_date", widget=DatePickerInput()),
        FieldPanel("end_date", widget=DatePickerInput()),
        FieldPanel("paid"),
        FieldPanel("braintree_subscription_id"),
    ]

    def __str__(self):
        return f"subscription {self.id}"

    @property
    def subscriber_full_name(self):
        full_name = ""

        if self.subscriber_given_name:
            full_name += self.subscriber_given_name + " "
        if self.subscriber_family_name:
            full_name += self.subscriber_family_name + " "

        return full_name.rstrip()

    def get_total_cost(self):
        return self.price

    def save(self, *args, **kwargs):
        self.price = SUBSCRIPTION_PRICE_COMPONENTS[self.price_group][self.format]

        super().save(*args, **kwargs)


class SubscriptionIndexPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
    ]

    subpage_types = []

    max_count = 1

    template = "subscription/index.html"

    def serve(self, request, *args, **kwargs):
        if request.method == "POST":
            # Avoid circular dependency
            from .forms import SubscriptionCreateForm

            subscription_form = SubscriptionCreateForm(request.POST)

            if subscription_form.is_valid():
                return process_subscription_form(subscription_form, request)
            else:
                context = self.get_context(request, *args, **kwargs)

                # Send form with validation errors back to client
                context["form"] = subscription_form

                return TemplateResponse(
                    request,
                    self.get_template(request, *args, **kwargs),
                    context
                )
        else:
            return super().serve(request)

    def get_context(self, request, *args, **kwargs):
        # avoid circular dependency
        from .forms import SubscriptionCreateForm

        context = super().get_context(request)

        # Pass in subscription form only if it isn't present
        # from previous validation in serve()
        if "form" not in context:
            context["form"] = SubscriptionCreateForm

        # Pass subscription pricing components to template
        context["subscription_price_components"] = SUBSCRIPTION_PRICE_COMPONENTS

        return context


class ManageSubscriptionPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
    ]

    subpage_types = []

    max_count = 1

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request)

        if request.user.is_authenticated:
            subscriptions = Subscription.objects.filter(user=request.user)

            context["subscriptions"] = subscriptions

        return context
