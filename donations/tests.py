from django.test import TestCase, RequestFactory
from .forms import DonationForm, DonorAddressForm
from django.urls import reverse
from .models import process_donation_forms, DonatePage, Donation
from django.http import HttpResponseRedirect
from wagtail.models import Page


class DonationModelTest(TestCase):
    def test_donation_created(self) -> None:
        # Create and save Donation object
        donation = Donation(amount=100, recurrence="monthly")
        donation.save()

        # Test that object attributes are equal to those set
        self.assertEqual(donation.amount, 100)
        self.assertEqual(donation.recurrence, "monthly")

    def test_process_donation_request_works_correctly(self) -> None:
        # Create completed form objects
        donation_form = DonationForm(
            {
                "amount": 100,
                "donor_given_name": "test_given_name",
                "donor_family_name": "test_family_name",
                "donor_email": "test@test.com",
                "recurrence": "monthly",
            }
        )

        donor_address_form = DonorAddressForm(
            {
                "street_address": "123 Main Street",
                "extended_address": "Apartment 1A",
                "locality": "Test Locality",
                "region": "Test Region",
                "postal_code": "12345",
                "country": "Testistan",
            }
        )

        # Create response using completed form objects
        response = process_donation_forms(
            donation_form,
            donor_address_form,
        )

        # Test that response is an HttpResponseRedirect
        self.assertIsInstance(response, HttpResponseRedirect)

        # Test that the response redirects to correct URL
        expected_url = reverse(
            "payment:process_donation_payment",
            kwargs={"donation_id": "3"},
        )
        self.assertEqual(response.url, expected_url)

    def test_total_cost_method(self) -> None:
        # Create donation object with specified amount
        donation = Donation(amount=100)

        # Test that get_total_cost returns specified amount
        self.assertEqual(donation.get_total_cost(), 100)

    def test_recurring(self) -> None:
        # Create donations with each recurrence possibility
        donation_monthly = Donation(
            amount=100, recurrence=Donation.DonationRecurrenceChoices.MONTHLY
        )
        donation_yearly = Donation(
            amount=200, recurrence=Donation.DonationRecurrenceChoices.YEARLY
        )
        donation_once = Donation(
            amount=300, recurrence=Donation.DonationRecurrenceChoices.ONCE
        )

        # Test that recurring() returns True for monthly and yearly donations
        self.assertTrue(donation_monthly.recurring())
        self.assertTrue(donation_yearly.recurring())

        # Test that recurring() returns False for once donation
        self.assertFalse(donation_once.recurring())


class DonatePageTest(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.donate_page = DonatePage(
            title="Donate", slug="donate", path="00010001", depth=2, numchild=0
        )
        self.home_page = Page.objects.get(slug="home")
        self.home_page.add_child(instance=self.donate_page)

    def test_serve_with_get(self) -> None:
        request = self.factory.get("/donate/")
        response = self.donate_page.serve(request)

        # Test that the response contains the donor_address_form in the context
        self.assertIn("donor_address_form", response.context_data)

    def test_serve_with_post_with_valid_data(self) -> None:
        # Create post request with DonationForm and DonorAddressForm data
        request = self.factory.post(
            "/donate/",
            data={
                "amount": 100,
                "donor_given_name": "test_given_name",
                "donor_family_name": "test_family_name",
                "donor_email": "test@test.com",
                "recurrence": "monthly",
                "street_address": "123 Main Street",
                "extended_address": "Apartment 1A",
                "locality": "Test Locality",
                "region": "Test Region",
                "postal_code": "12345",
                "country": "Testistan",
            },
        )

        # Add session to the request
        request.session = self.client.session
        request.session.save()

        # Serve the request
        response = self.donate_page.serve(request)

        # Test that the response is a redirect
        self.assertEqual(response.status_code, 302)

        # Test that the redirect URL is the donate page
        self.assertEqual(response.url, "/payment/process/donation/1")

        # Get donation object associated with donor address
        donation = Donation.objects.get(donor_address__street_address="123 Main Street")
        # Test that the retrieved donation object's donor
        # address is the same as the one provided in the form
        self.assertEqual(donation.donor_address.street_address, "123 Main Street")

    def test_serve_with_post_with_invalid_data(self) -> None:
        # Make a POST request to the donation page with the form data
        response = self.client.post(
            "/donate/",
            data={
                "amount": 100,
                "donor_given_name": "",  # Invalid donor_given_name
                "donor_family_name": "test_family_name",
                "donor_email": "test@test.com",
                "recurrence": "monthly",
                "street_address": "123 Main Street",
                "extended_address": "Apartment 1A",
                "locality": "Test Locality",
                "region": "Test Region",
                "postal_code": "12345",
                "country": "Testistan",
            },
        )

        # Test that the request was successful
        self.assertEqual(response.status_code, 200)

        # Try to retrieve the donation object associated with the provided donor address
        # Test that it is does not exist
        with self.assertRaises(Donation.DoesNotExist):
            Donation.objects.get(donor_given_name="")
