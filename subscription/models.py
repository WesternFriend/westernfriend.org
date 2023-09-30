import datetime
import logging
from typing import TYPE_CHECKING, Any


from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser
from django.db import models
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django_flatpickr.widgets import DatePickerInput
from wagtail.admin.panels import FieldPanel, FieldRowPanel, MultiFieldPanel
from wagtail.fields import RichTextField
from wagtail.models import Page

if TYPE_CHECKING:
    from .forms import SubscriptionCreateForm  # pragma: no cover

logger = logging.getLogger(__name__)


if TYPE_CHECKING:
    from accounts.models import User  # pragma: no cover


class MagazineFormatChoices(models.TextChoices):
    PDF = "pdf", "PDF"
    PRINT = "print", "Print"
    PRINT_AND_PDF = "print_and_pdf", "Print and PDF"


class MagazinePriceGroupChoices(models.TextChoices):
    BASIC = "basic", "Basic"
    TRUE_COST = "true_cost", "True cost"
    LOW_INCOME = "low_income", "Low income"
    INTERNATIONAL = "international", "International"


SUBSCRIPTION_PRICE_COMPONENTS = {
    "basic": {
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


def one_year_from_today() -> datetime.date:
    return datetime.date.today() + datetime.timedelta(days=365)


def process_subscription_form(
    subscription_form: "SubscriptionCreateForm",
    user: "User",
) -> "Subscription":
    """Given a valid subscription form, will save and associate with a user.

    TODO: determine how to share this function with the "manage subscription" page
    """
    # Create a temporary subscription object to modify it's fields
    subscription = subscription_form.save(commit=False)

    # Attach request user to subscription before save
    subscription.user = user

    # Set subscription start and end dates
    # based on current day
    today = datetime.date.today()

    # Start date is today
    subscription.start_date = today

    # End date is today
    # until we get a success message from the payment processor
    subscription.end_date = today

    subscription.save()

    return subscription


class Subscription(models.Model):
    magazine_format = models.CharField(
        max_length=255,
        choices=MagazineFormatChoices.choices,
        default="pdf",
    )
    price_group = models.CharField(
        max_length=255,
        choices=MagazinePriceGroupChoices.choices,
        default="basic",
    )
    price = models.IntegerField(
        editable=False,
    )
    recurring = models.BooleanField(
        default=True,
    )
    start_date = models.DateField(
        default=datetime.date.today,
    )
    end_date = models.DateField(
        default=one_year_from_today,
    )
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
    subscriber_organization = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )
    subscriber_street_address = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="The street address where a print subscription could be mailed",
    )
    subscriber_street_address_line_2 = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="If needed, second line for mailing address",
    )
    subscriber_postal_code = models.CharField(
        max_length=16,
        help_text="Postal code for the mailing address",
        blank=True,
    )
    subscriber_address_locality = models.CharField(
        max_length=255,
        help_text="City for the mailing address",
        blank=True,
    )
    subscriber_address_region = models.CharField(
        max_length=255,
        help_text="State for the mailing address",
        blank=True,
        default="",
    )
    subscriber_address_country = models.CharField(
        max_length=255,
        default="United States",
        help_text="Country for mailing",
        blank=True,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="subscriber",
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
        help_text="DO NOT EDIT. Used to cross-reference subscriptions with Braintree payments.",  # noqa: E501
    )

    panels = [
        MultiFieldPanel(
            heading="Subscriber details",
            children=[
                FieldPanel("user"),
                FieldRowPanel(
                    children=[
                        FieldPanel("subscriber_given_name"),
                        FieldPanel("subscriber_family_name"),
                    ],
                ),
            ],
        ),
        MultiFieldPanel(
            heading="Subscription details",
            children=[
                FieldRowPanel(
                    children=[
                        FieldPanel("magazine_format"),
                        FieldPanel("price_group"),
                        FieldPanel("paid"),
                    ],
                ),
                FieldRowPanel(
                    children=[
                        FieldPanel(
                            "start_date",
                            widget=DatePickerInput(),
                        ),
                        FieldPanel(
                            "end_date",
                            widget=DatePickerInput(),
                        ),
                    ],
                ),
                # TODO: make this field read_only=True with Wagtail 5.1 update
                FieldPanel(
                    "braintree_subscription_id",
                    read_only=True,
                ),
            ],
        ),
        MultiFieldPanel(
            heading="Subscriber postal address",
            children=[
                FieldPanel("subscriber_street_address"),
                FieldPanel("subscriber_street_address_line_2"),
                FieldRowPanel(
                    children=[
                        FieldPanel("subscriber_postal_code"),
                        FieldPanel("subscriber_address_locality"),
                    ],
                ),
                FieldRowPanel(
                    children=[
                        FieldPanel("subscriber_address_region"),
                        FieldPanel("subscriber_address_country"),
                    ],
                ),
            ],
        ),
    ]

    def __str__(self) -> str:
        return f"Subscription {self.id}"  # type: ignore

    @property
    def subscriber_full_name(self) -> str:
        """Return the full name of the subscriber."""

        name_components = [
            self.subscriber_given_name,
            self.subscriber_family_name,
        ]

        if all(name == "" for name in name_components):
            return ""
        else:
            return " ".join(name_components).strip()

    def get_total_cost(self) -> int:
        """Return the total cost of the subscription.

        This method is created to have a common interface for all money-
        related models. (Subscription, Donation, etc.)
        """
        return self.price

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Override save method to set price based on price group and
        format."""
        self.price = SUBSCRIPTION_PRICE_COMPONENTS[self.price_group][
            self.magazine_format
        ]

        super().save(*args, **kwargs)


class SubscriptionIndexPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
    ]

    parent_page_types = ["home.HomePage"]
    subpage_types: list[str] = []

    max_count = 1

    template = "subscription/index.html"

    def serve(
        self,
        request: HttpRequest,
        *args: tuple,
        **kwargs: dict,
    ) -> HttpResponse:
        # Make sure POST requests only come from authenticated users
        user_is_anonymous = (
            not hasattr(request, "user") or request.user.is_anonymous  # type: ignore
        )

        if request.method == "POST" and user_is_anonymous:
            login_base_url = reverse("login")[:-1]
            return redirect(f"{login_base_url}?next={request.path}")

        # Handle POST requests by authenticated users
        if request.method == "POST" and request.user.is_authenticated:
            user: AbstractBaseUser = request.user  # type: ignore

            # Avoid circular dependency
            from .forms import SubscriptionCreateForm

            subscription_form = SubscriptionCreateForm(request.POST)

            if subscription_form.is_valid():
                subscription: "Subscription" = process_subscription_form(
                    subscription_form=subscription_form,
                    user=user,  # type: ignore
                )

                # redirect for payment
                return redirect(
                    reverse(
                        "payment:process_subscription_payment",
                        kwargs={
                            "subscription_id": subscription.id,  # type: ignore
                        },
                    ),
                )

            context = self.get_context(request, *args, **kwargs)  # type: ignore

            # Send form with validation errors back to client
            context["form"] = subscription_form

            return TemplateResponse(
                request,
                self.get_template(request, *args, **kwargs),
                context,
            )
        else:
            return super().serve(request)

    def get_context(
        self,
        request: HttpRequest,
        *args: tuple,
        **kwargs: dict,
    ) -> dict[str, Any]:
        # avoid circular dependency
        from .forms import SubscriptionCreateForm

        context = super().get_context(request)

        # Pass in subscription form only if it isn't present
        # from previous validation in serve()
        if "form" not in context:
            context["form"] = SubscriptionCreateForm()

        # Pass subscription pricing components to template
        context["subscription_price_components"] = SUBSCRIPTION_PRICE_COMPONENTS

        return context


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
