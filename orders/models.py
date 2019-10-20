from django.db import models

from wagtail.admin.edit_handlers import FieldPanel, InlinePanel
from wagtail.core import blocks
from wagtail.core.fields import StreamField
from wagtail.core.models import Orderable, Page
from wagtail.snippets.models import register_snippet

from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel

from shipping.calculator import get_book_shipping_cost


class Order(ClusterableModel):
    purchaser_given_name = models.CharField(
        max_length=255, default="", help_text="Enter the given name for the purchaser."
    )
    purchaser_family_name = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Enter the family name for the purchaser.",
    )
    purchaser_email = models.EmailField(
        help_text="Provide an email, so we can communicate any issues regarding this order."
    )
    recipient_given_name = models.CharField(
        max_length=255, default="", help_text="Enter the given name for the recipient."
    )
    recipient_family_name = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Enter the family name for the recipient.",
    )
    recipient_street_address = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="The street address where this order should be shipped.",
    )
    recipient_postal_code = models.CharField(
        max_length=16, help_text="Postal code for the shipping address."
    )
    recipient_po_box_number = models.CharField(
        max_length=32, blank=True, default="", help_text="P.O. Box, if relevant."
    )
    recipient_address_locality = models.CharField(
        max_length=255, help_text="City for the shipping address."
    )
    recipient_address_region = models.CharField(
        max_length=255, help_text="State for the shipping address."
    )
    recipient_address_country = models.CharField(
        max_length=255, default="United States", help_text="Country for shipping."
    )
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2)
    paid = models.BooleanField(default=False)

    braintree_id = models.CharField(max_length=255, blank=True)

    panels = [
        FieldPanel("purchaser_given_name"),
        FieldPanel("purchaser_family_name"),
        FieldPanel("purchaser_email"),
        FieldPanel("recipient_given_name"),
        FieldPanel("recipient_family_name"),
        FieldPanel("recipient_street_address"),
        FieldPanel("recipient_po_box_number"),
        FieldPanel("recipient_postal_code"),
        FieldPanel("recipient_address_locality"),
        FieldPanel("recipient_address_region"),
        FieldPanel("recipient_address_country"),
        FieldPanel("shipping_cost"),
        FieldPanel("paid"),
        InlinePanel("items", label="Order items"),
    ]

    def __str__(self):
        return f"Order {self.id}"

    def get_total_cost(self):
        return sum(item.get_cost() for item in self.items.all())

    @property
    def recipient_full_name(self):
        return f"{self.recipient_given_name} {self.recipient_family_name}"
    
    @property
    def purchaser_full_name(self):
        return f"{self.purchaser_given_name} {self.purchaser_family_name}"


class OrderItem(Orderable):
    order = ParentalKey(
        Order, related_name="items", on_delete=models.CASCADE, blank=False
    )
    product_title = models.CharField(max_length=255)
    product_id = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    panels = [FieldPanel("product_title"), FieldPanel("price"), FieldPanel("quantity")]

    def __str__(self):
        return f"{self.quantity}x {self.product_title} @ { self.price}"

    def get_cost(self):
        return self.price * self.quantity
