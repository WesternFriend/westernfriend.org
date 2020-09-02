import datetime
import logging
import os

import braintree

from django.conf import settings
from django.contrib.auth import login
from django.db import models
from django.shortcuts import redirect
from django.urls import reverse

from wagtail.admin.edit_handlers import FieldPanel
from wagtail.core.fields import RichTextField
from wagtail.core.models import Page


from flatpickr import DatePickerInput

logger = logging.getLogger(__name__)


SUBSCRIPTION_TYPES_AND_PRICES = [
    {
        "slug": "print-only-regular-price",
        "name": "Print only - regular price",
        "price": 36,
    },
    {
        "slug": "print-only-true-cost",
        "name": "Print only - true cost price",
        "price": 72,
    },
    {
        "slug": "pdf-only-regular-price",
        "name": "PDF only - regular price",
        "price": 30,
    },
    {"slug": "pdf-only-true-cost", "name": "PDF only - true cost price", "price": 60,},
    {
        "slug": "print-and-pdf-regular-price",
        "name": "Both print and PDF - regular price",
        "price": 48,
    },
    {
        "slug": "print-and-pdf-true-cost",
        "name": "Both print and PDF -true cost price",
        "price": 96,
    },
]


def get_subscription_price(slug, SUBSCRIPTION_TYPES_AND_PRICES):
    matching_subscription_option = next(
        filter(lambda option: option["slug"] == slug, SUBSCRIPTION_TYPES_AND_PRICES)
    )

    return matching_subscription_option["price"]


def create_subscription_type_choices(SUBSCRIPTION_TYPES_AND_PRICES):
    subscription_type_choices = []

    for subscription in SUBSCRIPTION_TYPES_AND_PRICES:
        choice_label = f"{subscription['name']} - ${subscription['price']}"

        choice = (
            subscription["slug"],
            choice_label,
        )

        subscription_type_choices.append(choice)

    return subscription_type_choices


subscription_type_choices = create_subscription_type_choices(
    SUBSCRIPTION_TYPES_AND_PRICES
)

SUBSCRIPTION_DURATIONS_AND_DISCOUNTS = [
    {"duration": 1, "label": "One year", "discount": 0,},
    {"duration": 2, "label": "Two years", "discount": 10,},
    {"duration": 3, "label": "Three years", "discount": 25,},
]


def create_duration_choices(SUBSCRIPTION_DURATIONS_AND_DISCOUNTS):
    duration_choices = []

    for option in SUBSCRIPTION_DURATIONS_AND_DISCOUNTS:
        choice_key = option["duration"]

        if option["discount"] > 0:
            choice_label = f"{option['label']} (${option['discount']} discount)"
        else:
            choice_label = option["label"]

        choice = (choice_key, choice_label)

        duration_choices.append(choice)

    return duration_choices


duration_choices = create_duration_choices(SUBSCRIPTION_DURATIONS_AND_DISCOUNTS)


def get_subscription_option(duration, SUBSCRIPTION_DURATIONS_AND_DISCOUNTS):
    matching_option = filter(
        lambda option: option["duration"] == duration,
        SUBSCRIPTION_DURATIONS_AND_DISCOUNTS,
    )

    return next(matching_option)


class Subscription(models.Model):
    subscription_type = models.CharField(
        max_length=255,
        help_text="Choose the subscription type you would like to receive.",
        choices=subscription_type_choices,
    )
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
        FieldPanel("subscription_type"),
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

    @property
    def price(self):
        slug = self.subscription_type

        return get_subscription_price(slug, SUBSCRIPTION_TYPES_AND_PRICES)

    def get_total_cost(self):
        return self.price


class SubscriptionIndexPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
    ]

    subpage_types = []

    max_count = 1

    template = "subscription/index.html"

    def get_context(self, request, *args, **kwargs):
        # avoid circular dependency
        from .forms import UserRegisterationForm, SubscriptionCreateForm

        context = super().get_context(request)

        show_registration_form = request.GET.get("register")

        if show_registration_form:
            context["registration_form"] = UserRegisterationForm

        context["form"] = SubscriptionCreateForm

        return context

    def serve(self, request, *args, **kwargs):
        if request.method == "POST":
            user_is_registering = request.GET.get("register")

            # return the output of the form processing function
            # so this serve method returns an HttpResponse
            if user_is_registering:
                return process_registration_form(request)
            else:
                return process_subscription_form(request)
        else:
            return super().serve(request)


class ManageSubscriptionPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
    ]

    subpage_types = []

    max_count = 1

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request)

        if request.get("user"):
            subscriptions = Subscription.objects.filter(user=request.user)

            context["subscriptions"] = subscriptions

        return context


def process_registration_form(request):
    # Avoid circular dependency
    from .forms import UserRegisterationForm

    form = UserRegisterationForm(request.POST)

    if form.is_valid():
        user = form.save()

        login(request, user)

        return redirect("/subscribe")


def process_subscription_form(request):
    # Avoid circular dependency
    from .forms import SubscriptionCreateForm

    form = SubscriptionCreateForm(request.POST)

    if form.is_valid():
        # Create a temporary subscription object to modify it's fields
        subscription = form.save(commit=False)

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
