from decimal import Decimal

from django.contrib.postgres.fields import ArrayField
from django.db import models, transaction
from django.utils import timezone
from modelcluster.fields import ParentalKey  # type: ignore
from modelcluster.models import ClusterableModel  # type: ignore
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting
from wagtail.models import Orderable


def get_default_notification_emails():
    """Return default notification email list."""
    return ["editor@westernfriend.org"]


@register_setting
class BookstoreOrderNotificationSettings(BaseSiteSetting):
    """
    Settings for bookstore order email notifications.

    Configure which email addresses should receive notifications when
    bookstore orders are successfully paid.

    Note: This can be moved to a dedicated Notifications section if other
    notification types are added in the future.
    """

    notification_emails = ArrayField(
        models.EmailField(),
        default=get_default_notification_emails,
        blank=True,
        help_text=(
            "Email addresses that will receive notifications when bookstore "
            "orders are paid. One email per line. Default: editor@westernfriend.org"
        ),
    )

    panels = [
        FieldPanel("notification_emails"),
    ]

    class Meta:
        verbose_name = "Bookstore Order Notifications"


class Order(ClusterableModel):
    purchaser_given_name = models.CharField(
        max_length=255,
        default="",
        help_text="Enter the given name for the purchaser.",
        blank=True,
    )
    purchaser_family_name = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Enter the family name for the purchaser.",
    )
    purchaser_meeting_or_organization = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Enter the meeting or organization name, if this purchaser is a meeting or organization.",  # noqa: E501
    )
    purchaser_email = models.EmailField(
        help_text="Provide an email, so we can communicate any issues regarding this order.",  # noqa: E501
    )
    recipient_name = models.CharField(
        max_length=255,
        default="",
        help_text="Enter the recipient name (as it should appear on shipping label).",
    )
    recipient_street_address = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Reicipient street address and/or PO box",
    )
    recipient_postal_code = models.CharField(
        max_length=16,
        help_text="Postal code for the shipping address.",
    )
    recipient_address_locality = models.CharField(
        max_length=255,
        help_text="City for the shipping address.",
    )
    recipient_address_region = models.CharField(
        max_length=255,
        help_text="State for the shipping address.",
        blank=True,
        default="",
    )
    recipient_address_country = models.CharField(
        max_length=255,
        default="United States",
        help_text="Country for shipping.",
        choices=[
            ("United States", "United States"),
        ],
    )
    shipping_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    paid = models.BooleanField(default=False)
    paypal_order_id = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )
    paypal_payment_id = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )
    paypal_transaction_id = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    notification_sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when the order paid notification email was sent.",
    )

    class Meta:
        indexes = [
            models.Index(
                fields=["paypal_order_id"],
            ),
        ]

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("purchaser_given_name"),
                FieldPanel("purchaser_family_name"),
                FieldPanel("purchaser_meeting_or_organization"),
                FieldPanel("purchaser_email"),
            ],
            heading="Purchaser",
        ),
        MultiFieldPanel(
            [
                FieldPanel("recipient_name"),
                FieldPanel("recipient_street_address"),
                FieldPanel("recipient_postal_code"),
                FieldPanel("recipient_address_locality"),
                FieldPanel("recipient_address_region"),
                FieldPanel("recipient_address_country"),
            ],
            heading="Recipient",
        ),
        MultiFieldPanel(
            [
                FieldPanel(
                    "paypal_transaction_id",
                    read_only=True,
                ),
                FieldPanel("paid"),
                FieldPanel("shipping_cost"),
            ],
            heading="PayPal Payment Info",
        ),
        InlinePanel("items", label="Order items"),
    ]

    def __str__(self) -> str:
        return f"Order {self.id}"  # type: ignore

    def get_total_items_cost(self) -> Decimal:
        """Return the sum of all order items' costs."""
        # order.items is of type list[OrderItem]

        items_cost = sum(
            [item.get_cost() for item in self.items.all()],
        )

        return Decimal(items_cost).quantize(Decimal("0.01"))

    def get_total_cost(self) -> Decimal:
        """Return the sum of all order items' costs, plus shipping cost."""
        return self.get_total_items_cost() + Decimal(self.shipping_cost)

    @property
    def purchaser_full_name(self) -> str:
        full_name = ""

        if self.purchaser_given_name:
            full_name += self.purchaser_given_name + " "
        if self.purchaser_family_name:
            full_name += self.purchaser_family_name + " "
        if self.purchaser_meeting_or_organization:
            full_name += self.purchaser_meeting_or_organization
        # Combine any available name data, removing leading or trailing whitespace
        return full_name.rstrip()

    def save(self, *args, **kwargs):
        """
        Override save to send email notification when order is marked as paid.

        Sends notification only once (when paid=True and notification_sent_at is None).
        Uses transaction.on_commit() to ensure notification is sent after database commit.
        """
        # Check if we need to send notification
        should_notify = self.paid and self.notification_sent_at is None

        # If we're going to notify, set the timestamp now to prevent duplicates
        # if the same instance is saved again
        if should_notify:
            self.notification_sent_at = timezone.now()

        # Save the order
        super().save(*args, **kwargs)

        # Schedule notification after transaction commits
        if should_notify:
            # Import inside method to avoid circular import
            from orders.notifications import send_order_paid_notification

            # Use on_commit to ensure notification is sent after successful database commit
            transaction.on_commit(lambda: send_order_paid_notification(self))


class OrderItem(Orderable):
    order = ParentalKey(
        Order,
        related_name="items",
        on_delete=models.CASCADE,
        blank=False,
    )
    product_title = models.CharField(
        max_length=255,
    )
    product_id = models.PositiveIntegerField(
        default=1,
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    quantity = models.PositiveIntegerField(
        default=1,
    )

    panels = [
        FieldPanel("product_title"),
        FieldPanel("price"),
        FieldPanel("quantity"),
    ]

    def __str__(self) -> str:
        return f"{self.quantity}x {self.product_title} @ {round(self.price, 2)}/each"  # noqa: E501

    def get_cost(self) -> Decimal:
        """Return the total cost for this order item."""
        total_cost = self.price * self.quantity

        return Decimal(total_cost).quantize(Decimal("0.01"))
