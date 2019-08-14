from django.db import models

from wagtail.admin.edit_handlers import FieldPanel, InlinePanel
from wagtail.core import blocks
from wagtail.core.fields import StreamField
from wagtail.core.models import Orderable, Page
from wagtail.snippets.models import register_snippet

from modelcluster.fields import (
    ParentalKey,
)
from modelcluster.models import ClusterableModel


class Order(ClusterableModel):
    given_name = models.CharField(
        max_length=255,
        default="",
        help_text="Enter the given name for a person.",
    )
    family_name = models.CharField(max_length=255, blank=True, default="")
    email = models.EmailField()
    postal_address = models.TextField()
    paid = models.BooleanField(default=False)

    panels = [
        FieldPanel("given_name"),
        FieldPanel("family_name"),
        FieldPanel("email"),
        FieldPanel("postal_address"),
        FieldPanel("paid"),
        InlinePanel("items", label="Order items"),
    ]

    def __str__(self):
        return f"Order {self.id}"

    def get_total_cost(self):
        return sum(item.get_cost() for item in self.items.all())

    @property
    def full_name(self):
        return f"{self.given_name} {self.family_name}"


class OrderItem(Orderable):
    order = ParentalKey(
        Order,
        related_name="items",
        on_delete=models.CASCADE,
        blank=False,
    )
    product = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    panels = [
        FieldPanel("product"),
        FieldPanel("price"),
        FieldPanel("quantity"),
    ]

    def __str__(self):
        return f"{self.quantity}x {self.product} @ { self.price}"

    def get_cost(self):
        return self.price * self.quantity
