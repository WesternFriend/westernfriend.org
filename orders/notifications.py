import logging

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

from orders.models import BookstoreOrderNotificationSettings, Order

logger = logging.getLogger(__name__)


def send_order_paid_notification(order: Order) -> bool:
    """
    Send email notification when a bookstore order is successfully paid.

    Args:
        order: The Order instance that was paid

    Returns:
        bool: True if notification was sent successfully, False otherwise

    Note:
        All exceptions are caught and logged to Sentry without re-raising.
        After successful send, updates order.notification_sent_at timestamp.
    """
    try:
        # Get notification settings for the default site
        from wagtail.models import Site

        try:
            site = Site.objects.get(is_default_site=True)
        except Site.DoesNotExist:
            # If no default site, try to get any site
            site = Site.objects.first()

        if site is None:
            logger.warning("No site found, cannot send order notification.")
            return False

        notification_settings = BookstoreOrderNotificationSettings.for_site(site)

        # Skip if no emails configured
        if not notification_settings.notification_emails:
            logger.warning(
                f"No notification emails configured for order #{order.id}. "  # type: ignore
                "Skipping notification.",
            )
            return False

        # Construct admin URL for viewing the order
        admin_base_url = settings.WAGTAILADMIN_BASE_URL
        admin_url = f"{admin_base_url}/store/bookstore_orders/inspect/{order.id}/"  # type: ignore

        # Prepare email context
        context = {
            "order": order,
            "admin_url": admin_url,
        }

        # Render email templates
        subject = render_to_string(
            "orders/emails/order_paid_notification_subject.txt",
            context,
        ).strip()

        text_message = render_to_string(
            "orders/emails/order_paid_notification_email.txt",
            context,
        )

        html_message = render_to_string(
            "orders/emails/order_paid_notification_email.html",
            context,
        )

        # Send email to all configured recipients
        send_mail(
            subject=subject,
            message=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=notification_settings.notification_emails,
            html_message=html_message,
            fail_silently=False,
        )

        # Update notification timestamp using update() to avoid triggering save() again
        Order.objects.filter(pk=order.pk).update(notification_sent_at=timezone.now())

        logger.info(
            f"Order paid notification sent successfully for order #{order.id} "  # type: ignore
            f"to {len(notification_settings.notification_emails)} recipient(s).",
        )

        return True

    except Exception as e:
        # Log all exceptions to Sentry without re-raising
        logger.exception(
            f"Failed to send order paid notification for order #{order.id}: {str(e)}",  # type: ignore
        )
        return False
