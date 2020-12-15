from django.db import models
from django.shortcuts import redirect
from django.urls import reverse

from wagtail.admin.edit_handlers import FieldPanel, StreamFieldPanel
from wagtail.core.blocks import IntegerBlock
from wagtail.core.fields import RichTextField, StreamField
from wagtail.core.models import Page


def process_donation_form(donation_form, request):
    """
    Process a donation form and redirecto to payment.
    """
    # Create a temporary donation object to modify it's fields
    donation = donation_form.save(commit=False)

    # TODO: create address instance and associate it with donatino
    # address = Address()
    # donation.address = address

    # Save donation with associated address
    donation.save()

    # set the order in the session
    request.session["donation"] = donation.id

    # redirect for payment
    return redirect(
        reverse("payment:process", kwargs={"previous_page": "donate"})
    )


class DonatePage(Page):
    intro = RichTextField(blank=True)
    suggested_donation_amounts = StreamField([
        ("amount", IntegerBlock())
    ], null=True, blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro", classname="full"),
        StreamFieldPanel("suggested_donation_amounts")
    ]

    max_count = 1

    def serve(self, request, *args, **kwargs):
        if request.method == "POST":
            # Avoid circular dependency
            from .forms import DonationForm

            donation_form = DonationForm(request.POST)

            if donation_form.is_valid():
                return process_donation_form(donation_form, request)
            else:
                return super().serve(request)
        else:
            return super().serve(request)


class Donation(models.Model):
    amount = models.IntegerField()

    @property
    def price(self):
        # Add price property to conform to payment page
        return self.amount
