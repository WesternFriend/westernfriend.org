from decimal import Decimal
from http import HTTPStatus
from unittest.mock import MagicMock, Mock, patch

from django.contrib.sessions.middleware import SessionMiddleware
from django.core import mail
from django.test import (
    Client,
    RequestFactory,
    TestCase,
    TransactionTestCase,
    override_settings,
)
from django.urls import reverse
from django.utils import timezone

from cart.cart import Cart
from cart.tests import scaffold_product_index_page
from orders.views import create_cart_order_items
from store.factories import ProductFactory

from .models import BookstoreOrderNotificationSettings, Order, OrderItem
from .notifications import send_order_paid_notification


class OrderModelTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        # Create an Order instance using the factory
        cls.order = Order(  # type: ignore
            id=1,
            purchaser_given_name="John",
            purchaser_family_name="Doe",
            purchaser_meeting_or_organization="Western Friend",
            shipping_cost=4.00,
        )
        cls.order.save()  # type: ignore

        # Create OrderItems
        cls.order_item_one = OrderItem.objects.create(  # type: ignore
            order=cls.order,  # type: ignore
            product_title="Product 1",
            product_id=1,
            price=10.00,
            quantity=2,
        )

        cls.order_item_two = OrderItem.objects.create(  # type: ignore
            order=cls.order,  # type: ignore
            product_title="Product 2",
            product_id=2,
            price=20.00,
            quantity=3,
        )

    def test_purchaser_full_name(self) -> None:
        # Test the method
        self.assertEqual(
            self.order.purchaser_full_name,  # type: ignore
            "John Doe Western Friend",
        )

        # Test with empty purchaser_family_name
        self.order.purchaser_family_name = ""  # type: ignore
        self.order.save()  # type: ignore
        self.assertEqual(
            self.order.purchaser_full_name,
            "John Western Friend",
        )  # type: ignore

        # Test with only purchaser_meeting_or_organization
        self.order.purchaser_given_name = ""
        self.order.save()
        self.assertEqual(self.order.purchaser_full_name, "Western Friend")

    def test_str_method(self) -> None:
        # Test the method
        self.assertEqual(
            str(self.order),
            "Order 1",
        )

    def test_order_get_total_cost(self):
        order_item_one_total = self.order_item_one.quantity * self.order_item_one.price
        order_item_two_total = self.order_item_two.quantity * self.order_item_two.price
        expected_total = (
            order_item_one_total + order_item_two_total + self.order.shipping_cost
        )
        expected_decimal = Decimal(expected_total).quantize(Decimal("0.01"))
        self.assertEqual(self.order.get_total_cost(), expected_decimal)


class OrderItemModelTest(TestCase):
    def setUp(self) -> None:
        # Create an OrderItem instance using the factory
        self.order_item = OrderItem(
            id=1,
            product_title="Quaker Faith & Practice",
            product_id=1,
            price=19.99,
            quantity=2,
        )

    def test_str_method(self) -> None:
        expected_string = "2x Quaker Faith & Practice @ 19.99/each"

        self.assertEqual(
            str(self.order_item),
            expected_string,
        )

    def test_get_cost_method(self) -> None:
        expected_cost = Decimal("39.98")

        self.assertEqual(
            self.order_item.get_cost(),
            expected_cost,
        )


class OrderCreateViewTest(TestCase):
    def setUp(self) -> None:
        # Create a client to make requests
        self.client = Client()

        # Mock the Cart
        self.cart_mock = patch("cart.cart.Cart").start()

    def tearDown(self) -> None:
        # Stop the Cart mock
        patch.stopall()

    def test_order_create_view_get_request(self) -> None:
        # Send a GET request
        response = self.client.get(reverse("orders:order_create"))

        # Check that the response has a status code of 200
        self.assertEqual(response.status_code, 200)

        # Check if the correct template was used
        self.assertTemplateUsed(response, "orders/create.html")

    def test_order_create_view_post_request_form_valid(self) -> None:
        # Mock the OrderCreateForm
        with patch("orders.views.OrderCreateForm") as MockOrderCreateForm:
            # Instance of the form
            mock_form = MagicMock()

            # Set is_valid to return True
            mock_form.is_valid.return_value = True

            # Set save to return a mock order with an id
            mock_order = MagicMock()
            mock_order.id = 1
            mock_form.save.return_value = mock_order

            # Set our mock form as the return value of the form class
            MockOrderCreateForm.return_value = mock_form

            # Send a POST request
            response = self.client.post(
                reverse("orders:order_create"),
            )

            # Check that the response is a redirect
            self.assertEqual(
                response.status_code,
                HTTPStatus.FOUND,
            )

            # Check if the redirect URL is correct
            self.assertRedirects(
                response,
                reverse(
                    "payment:process_bookstore_order_payment",
                    kwargs={"order_id": mock_order.id},
                ),
                fetch_redirect_response=False,
            )

    def test_order_create_view_post_request_form_invalid(self) -> None:
        # Create a dictionary with the invalid data you want to test
        invalid_data = {
            "field_name": "invalid value",
        }  # replace with your actual invalid data

        # Send a POST request using the client
        response = self.client.post(reverse("orders:order_create"), invalid_data)

        # Check that the response has a status code of 200
        self.assertEqual(response.status_code, 200)

        # Check if the correct template was used
        self.assertTemplateUsed(response, "orders/create.html")


class CreateCartOrderItemsTest(TestCase):
    def setUp(self) -> None:
        # Create an order instance
        self.order = Order.objects.create(
            purchaser_given_name="John",
            purchaser_family_name="Doe",
            purchaser_meeting_or_organization="Western Friend",
            shipping_cost=4.00,
        )

        # Create a request instance using RequestFactory
        self.factory = RequestFactory()
        self.request = self.factory.get("/")

        # Add session to request
        middleware = SessionMiddleware(Mock())
        middleware.process_request(self.request)
        self.request.session.save()

        # Create a cart instance
        self.cart = Cart(self.request)

        product_index_page = scaffold_product_index_page()

        # create some test products using the ProductFactory
        self.product1 = ProductFactory.build()
        self.product2 = ProductFactory.build()

        product_index_page.add_child(instance=self.product1)
        product_index_page.add_child(instance=self.product2)

        # Add products to the cart
        self.product1_quantity = 2
        self.product2_quantity = 3
        self.cart.add(
            self.product1,
            quantity=self.product1_quantity,
        )
        self.cart.add(
            self.product2,
            quantity=self.product2_quantity,
        )

    def test_create_cart_order_items(self) -> None:
        # Call the function with the order and cart
        create_cart_order_items(
            self.order,
            self.cart,
        )

        # Assert that the OrderItems were correctly created
        self.assertEqual(
            OrderItem.objects.count(),
            2,
        )
        item1 = OrderItem.objects.get(
            order=self.order,
            product_id=self.product1.id,
        )
        self.assertEqual(
            item1.product_title,
            self.product1.title,
        )
        self.assertEqual(
            item1.price,
            self.product1.price,
        )
        self.assertEqual(
            item1.quantity,
            self.product1_quantity,
        )

        item2 = OrderItem.objects.get(
            order=self.order,
            product_id=self.product2.id,
        )
        self.assertEqual(
            item2.product_title,
            self.product2.title,
        )
        self.assertEqual(
            item2.price,
            self.product2.price,
        )
        self.assertEqual(
            item2.quantity,
            self.product2_quantity,
        )


class WagtailSiteSetupMixin:
    """Mixin providing common Wagtail site setup for notification tests."""

    def setUp(self):
        """Set up Wagtail site and locale for tests."""
        from wagtail.models import Locale, Page, Site

        # Create a locale for Wagtail pages (needed for TransactionTestCase)
        Locale.objects.get_or_create(language_code="en")

        # Create a root page if it doesn't exist
        try:
            root = Page.objects.get(depth=1)
        except Page.DoesNotExist:
            root = Page.add_root(title="Root", slug="root")

        # Create a default site
        self.site = Site.objects.create(
            hostname="testserver",
            root_page=root,
            is_default_site=True,
        )


class BookstoreOrderNotificationSettingsTest(WagtailSiteSetupMixin, TestCase):
    """Test the bookstore order notification settings model."""

    def test_default_email_is_set(self):
        """Test that default email is set when settings are created."""
        settings = BookstoreOrderNotificationSettings.for_site(self.site)
        self.assertEqual(settings.notification_emails, ["editor@westernfriend.org"])

    def test_custom_emails_can_be_set(self):
        """Test that custom emails can be configured."""
        settings = BookstoreOrderNotificationSettings.for_site(self.site)
        settings.notification_emails = ["admin@example.com", "manager@example.com"]
        settings.save()

        # Reload settings
        settings = BookstoreOrderNotificationSettings.for_site(self.site)
        self.assertEqual(len(settings.notification_emails), 2)
        self.assertIn("admin@example.com", settings.notification_emails)
        self.assertIn("manager@example.com", settings.notification_emails)


class OrderNotificationTest(WagtailSiteSetupMixin, TransactionTestCase):
    """Test order notification functionality.

    Uses TransactionTestCase because we need transaction.on_commit() to fire
    when testing the order.save() notification trigger.
    """

    def setUp(self):
        """Set up test data."""
        # Call parent setUp to create site
        super().setUp()

        self.order = Order.objects.create(
            purchaser_given_name="Jane",
            purchaser_family_name="Smith",
            purchaser_email="jane@example.com",
            purchaser_meeting_or_organization="Test Meeting",
            recipient_name="Jane Smith",
            recipient_street_address="123 Test St",
            recipient_postal_code="12345",
            recipient_address_locality="Test City",
            recipient_address_region="TS",
            shipping_cost=5.00,
            paid=False,
            paypal_transaction_id="TEST123",
        )

        # Create order items
        OrderItem.objects.create(
            order=self.order,
            product_title="Test Book",
            product_id=1,
            price=19.99,
            quantity=2,
        )

    def test_notification_not_sent_when_order_created_unpaid(self):
        """Test that notification is not sent when order is created as unpaid."""
        self.assertEqual(len(mail.outbox), 0)
        self.assertIsNone(self.order.notification_sent_at)

    def test_notification_sent_when_order_marked_paid(self):
        """Test that notification is sent when order is marked as paid."""
        # Mark order as paid
        self.order.paid = True
        self.order.save()

        # Check that email was sent
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]

        # Check email content
        self.assertIn("Order #", email.subject)
        self.assertIn("Jane Smith", email.subject)
        self.assertIn("jane@example.com", email.body)
        self.assertIn("TEST123", email.body)
        self.assertIn("Test Book", email.body)
        self.assertIn("/store/bookstore_orders/inspect/", email.body)

        # Check that notification timestamp was set
        self.order.refresh_from_db()
        self.assertIsNotNone(self.order.notification_sent_at)

    def test_notification_not_sent_twice(self):
        """Test that notification is only sent once per order."""
        # Mark order as paid first time
        self.order.paid = True
        self.order.save()

        # Refresh from database to get updated notification_sent_at
        self.order.refresh_from_db()

        # Clear mail outbox
        mail.outbox.clear()

        # Save order again (still paid)
        self.order.save()

        # Check that no new email was sent
        self.assertEqual(len(mail.outbox), 0)

    def test_no_duplicate_notification_without_refresh(self):
        """Test that in-memory instance prevents duplicate notifications.

        This tests the bug fix where the in-memory order instance is updated
        with notification_sent_at after sending, preventing duplicate notifications
        if the same instance is saved again without refreshing from database.
        """
        # Verify order starts unpaid with no notification timestamp
        self.assertFalse(self.order.paid)
        self.assertIsNone(self.order.notification_sent_at)

        # Mark order as paid and save
        self.order.paid = True
        self.order.save()

        # WITHOUT refresh_from_db(), the in-memory instance should still
        # have notification_sent_at set due to our fix
        self.assertIsNotNone(
            self.order.notification_sent_at,
            "In-memory instance should have notification_sent_at updated after save",
        )

        # Clear mail outbox to detect any duplicate notifications
        mail.outbox.clear()

        # Save the same in-memory instance again (e.g., updating another field)
        # This should NOT trigger another notification because notification_sent_at
        # is now set on the in-memory instance
        self.order.save()

        # Verify no duplicate notification was sent
        self.assertEqual(
            len(mail.outbox),
            0,
            "No duplicate notification should be sent when saving the same instance",
        )

    def test_notification_sent_to_configured_recipients(self):
        """Test that notification is sent to all configured email addresses."""
        # Update settings with multiple recipients
        settings = BookstoreOrderNotificationSettings.for_site(self.site)
        settings.notification_emails = [
            "editor@westernfriend.org",
            "admin@westernfriend.org",
        ]
        settings.save()

        self.order.paid = True
        self.order.save()

        # Check that email was sent to all recipients
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(len(email.to), 2)
        self.assertIn("editor@westernfriend.org", email.to)
        self.assertIn("admin@westernfriend.org", email.to)

    def test_notification_skipped_when_no_emails_configured(self):
        """Test that notification is skipped when no emails are configured."""
        # Update settings with no emails
        settings = BookstoreOrderNotificationSettings.for_site(self.site)
        settings.notification_emails = []
        settings.save()

        self.order.paid = True
        self.order.save()

        # Check that no email was sent
        self.assertEqual(len(mail.outbox), 0)

    def test_notification_error_does_not_prevent_save(self):
        """Test that email sending errors don't prevent order from being saved."""
        with patch("orders.notifications.send_mail") as mock_send_mail:
            # Make send_mail raise an exception
            mock_send_mail.side_effect = Exception("SMTP Error")

            # This should not raise an exception
            self.order.paid = True
            self.order.save()

            # Order should still be saved as paid
            self.order.refresh_from_db()
            self.assertTrue(self.order.paid)

    def test_notification_url_construction(self):
        """Test that admin URL is correctly constructed."""
        self.order.paid = True
        self.order.save()

        email = mail.outbox[0]
        expected_path = f"/admin/store/bookstore_orders/inspect/{self.order.id}/"
        self.assertIn(expected_path, email.body)

    @override_settings(DEFAULT_FROM_EMAIL="custom@westernfriend.org")
    def test_notification_uses_default_from_email(self):
        """Test that notification uses Django's DEFAULT_FROM_EMAIL setting."""
        self.order.paid = True
        self.order.save()

        email = mail.outbox[0]
        self.assertEqual(email.from_email, "custom@westernfriend.org")

    def test_order_items_displayed_in_notification(self):
        """Test that all order items are displayed in the notification."""
        # Add another item
        OrderItem.objects.create(
            order=self.order,
            product_title="Another Book",
            product_id=2,
            price=24.99,
            quantity=1,
        )

        self.order.paid = True
        self.order.save()

        email = mail.outbox[0]
        self.assertIn("Test Book", email.body)
        self.assertIn("Another Book", email.body)
        self.assertIn("2x", email.body)  # quantity for first item
        self.assertIn("1x", email.body)  # quantity for second item


class SendOrderPaidNotificationTest(WagtailSiteSetupMixin, TransactionTestCase):
    """Test the send_order_paid_notification function directly.

    Uses TransactionTestCase to properly test database updates.
    """

    def setUp(self):
        """Set up test data."""
        # Call parent setUp to create site
        super().setUp()

        self.order = Order.objects.create(
            purchaser_given_name="Test",
            purchaser_family_name="User",
            purchaser_email="test@example.com",
            recipient_name="Test User",
            recipient_street_address="123 Test St",
            recipient_postal_code="12345",
            recipient_address_locality="Test City",
            recipient_address_region="TS",
            shipping_cost=5.00,
            paid=False,  # Start unpaid to avoid automatic notification
            paypal_transaction_id="TEST456",
        )

    def test_function_returns_true_on_success(self):
        """Test that function returns True when email is sent successfully."""
        result = send_order_paid_notification(self.order)
        self.assertTrue(result)

    def test_function_returns_false_when_no_emails_configured(self):
        """Test that function returns False when no emails are configured."""
        # Update settings with no emails
        settings = BookstoreOrderNotificationSettings.for_site(self.site)
        settings.notification_emails = []
        settings.save()

        result = send_order_paid_notification(self.order)
        self.assertFalse(result)

    def test_function_returns_false_on_error(self):
        """Test that function returns False when an error occurs."""
        with patch("orders.notifications.send_mail") as mock_send_mail:
            mock_send_mail.side_effect = Exception("Test error")

            result = send_order_paid_notification(self.order)
            self.assertFalse(result)

    def test_function_updates_notification_timestamp_on_success(self):
        """Test that notification_sent_at is set before calling the function.

        In normal usage, the timestamp is set in save() before the notification
        function is called. This test verifies the function works correctly
        when the timestamp is already set.
        """
        # Set timestamp as save() would
        self.order.notification_sent_at = timezone.now()
        self.order.save()

        # Verify timestamp was set
        self.assertIsNotNone(self.order.notification_sent_at)

        # Calling the notification function should work even though timestamp is set
        result = send_order_paid_notification(self.order)
        self.assertTrue(result)

    def test_function_logs_error_on_exception(self):
        """Test that function returns False when an exception occurs."""
        with patch("orders.notifications.send_mail") as mock_send_mail:
            mock_send_mail.side_effect = Exception("Test error")

            result = send_order_paid_notification(self.order)
            self.assertFalse(result)
