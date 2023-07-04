from typing import TYPE_CHECKING
from django.db import models
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from wagtail.admin.panels import FieldPanel
from wagtail.blocks import IntegerBlock, ListBlock, StreamBlock, StructBlock
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Page

from addresses.models import Address

if TYPE_CHECKING:
    from .forms import DonationForm, DonorAddressForm  # pragma: no cover


def process_donation_forms(
    donation_form: "DonationForm",
    donor_address_form: "DonorAddressForm",
) -> HttpResponse:
    """Process a donation form and redirect to payment."""
    # Create a temporary donation object to modify it's fields
    donation = donation_form.save(commit=False)

    # Check if user submitted any address information
    if donor_address_form.is_valid():
        # Create donor address instance and associate it with donation
        donor_address = donor_address_form.save()

        donation.donor_address = donor_address

    # Save donation with associated address
    donation.save()

    # redirect for payment
    return redirect(
        reverse(
            "payment:process_donation_payment",
            kwargs={
                "donation_id": donation.id,
            },
        ),
    )


class SuggestedDonationAmountsBlock(StructBlock):
    once = ListBlock(IntegerBlock(label="Amount"))
    monthly = ListBlock(IntegerBlock(label="Amount"))
    yearly = ListBlock(IntegerBlock(label="Amount"))


class DonatePage(Page):
    intro = RichTextField(blank=True)
    suggested_donation_amounts = StreamField(
        StreamBlock(
            [
                (
                    "suggested_donation_amounts",
                    SuggestedDonationAmountsBlock(max_num=1),
                ),
            ],
            max_num=1,
        ),
        null=True,
        blank=True,
        use_json_field=True,
    )

    max_count = 1

    content_panels = Page.content_panels + [
        FieldPanel("suggested_donation_amounts"),
    ]

    parent_page_types = ["home.HomePage"]
    subpage_types: list[str] = []

    def serve(
        self,
        request: HttpRequest,
        *args: tuple,
        **kwargs: dict,
    ) -> HttpResponse:
        # Avoid circular dependency
        from .forms import DonationForm, DonorAddressForm

        donor_address_form = DonorAddressForm(request.POST)
        donation_form = DonationForm(request.POST)

        if request.method == "POST" and donation_form.is_valid():
            return process_donation_forms(
                donation_form,
                donor_address_form,
            )

        # Send donor address form to client
        # Note, we manually create the donation form in the template
        context = self.get_context(
            request,
            *args,
            **kwargs,
        )
        context["donor_address_form"] = donor_address_form

        return TemplateResponse(
            request,
            self.get_template(
                request,
                *args,
                **kwargs,
            ),
            context,
        )


class DonorAddress(Address):
    pass


class Donation(models.Model):
    class DonationRecurrenceChoices(models.TextChoices):
        ONCE = ("once", "Once")
        MONTHLY = ("monthly", "Monthly")
        YEARLY = ("yearly", "Yearly")

    amount = models.IntegerField()
    recurrence = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        choices=DonationRecurrenceChoices.choices,
        default=DonationRecurrenceChoices.ONCE,
    )
    donor_given_name = models.CharField(
        max_length=255,
    )
    donor_family_name = models.CharField(
        max_length=255,
    )
    donor_organization = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )
    donor_email = models.EmailField(
        help_text="Please enter your email",
    )
    donor_address = models.ForeignKey(
        to=DonorAddress,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    paid = models.BooleanField(default=False)
    braintree_transaction_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )
    braintree_subscription_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )
    # TODO: add date fields for created, payment_completed, updated

    def get_total_cost(self) -> int:
        # Add get_total_cost method to conform to payment page
        return self.amount

    @property
    def recurring(self) -> bool:
        """Determine whether Donation is recurring.

        Return True if Donation recurrence is "monthly" or "yearly",
        otherwise False
        """

        return self.recurrence in (
            self.DonationRecurrenceChoices.MONTHLY,
            self.DonationRecurrenceChoices.YEARLY,
        )
