from django.db import models

from wagtail.admin.edit_handlers import FieldPanel

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
    {
        "slug": "pdf-only-true-cost",
        "name": "PDF only - true cost price",
        "price": 60,
    },
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

def create_subscription_type_choices(SUBSCRIPTION_TYPES_AND_PRICES):
    subscription_type_choices = []

    for subscription in SUBSCRIPTION_TYPES_AND_PRICES:
        choice_label = f"{subscription['name']} - ${subscription['price']}" 
        
        choice = (
            subscription['slug'],
            choice_label,
        )

        subscription_type_choices.append(choice)

    return subscription_type_choices
    
subscription_type_choices = create_subscription_type_choices(SUBSCRIPTION_TYPES_AND_PRICES)

class Subscription(models.Model):
    subscription_type = models.CharField(
        max_length=255,
        help_text="Choose the subscription type you would like to receive.",
        choices=subscription_type_choices,
    )
    subscriber_given_name = models.CharField(
        max_length=255, default="", help_text="Enter the given name for the subscriber.", blank=True,
    )
    subscriber_family_name = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Enter the family name for the subscriber.",
    )
    subscriber_email = models.EmailField(
        help_text="Provide an email, so we can communicate any issues regarding this subscription."
    )
    subscriber_street_address = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="The street address where this subscription should be shipped.",
    )
    subscriber_postal_code = models.CharField(
        max_length=16, help_text="Postal code for the shipping address."
    )
    subscriber_po_box_number = models.CharField(
        max_length=32, blank=True, default="", help_text="P.O. Box, if relevant."
    )
    subscriber_address_locality = models.CharField(
        max_length=255, help_text="City for the shipping address."
    )
    subscriber_address_region = models.CharField(
        max_length=255, help_text="State for the shipping address.", blank=True, default=""
    )
    subscriber_address_country = models.CharField(
        max_length=255, default="United States", help_text="Country for shipping."
    )
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2)
    paid = models.BooleanField(default=False)

    braintree_id = models.CharField(max_length=255, blank=True)

    panels = [
        FieldPanel("subscription_type"),
        FieldPanel("subscriber_given_name"),
        FieldPanel("subscriber_family_name"),
        FieldPanel("subscriber_email"),
        FieldPanel("subscriber_street_address"),
        FieldPanel("subscriber_po_box_number"),
        FieldPanel("subscriber_postal_code"),
        FieldPanel("subscriber_address_locality"),
        FieldPanel("subscriber_address_region"),
        FieldPanel("subscriber_address_country"),
        FieldPanel("paid"),
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
