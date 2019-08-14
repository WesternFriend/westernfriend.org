from django.db import models

from wagtail.admin.edit_handlers import FieldPanel
from wagtail.core.models import Page


class Order(models.Model):
    given_name = models.CharField(
        max_length=255,
        default="",
        help_text="Enter the given name for a person.",
    )
    family_name = models.CharField(max_length=255, blank=True, default="")
    email = models.EmailField()
    postal_address = models.TextField()
    paid = models.BooleanField(default=False)

    content_panels = Page.content_panels + [
        FieldPanel("given_name"),
        FieldPanel("family_name"),
        FieldPanel("email"),
        FieldPanel("postal_address"),
        FieldPanel("paid"),
    ]

    def __str__(self):
        return f"Order {self.id}"

    def get_total_cost(self):
        return sum(item.get_cost() for item in self.items.all())

    @property
    def full_name(self):
        return f"{self.given_name} {self.family_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        related_name="items",
        on_delete=models.CASCADE
    )
    product = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.id}"

    def get_cost(self):
        return self.price * self.quantity
