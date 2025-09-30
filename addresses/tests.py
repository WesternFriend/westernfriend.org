from django.test import SimpleTestCase
from .models import Address


class TestAddress(Address):
    pass


class AddressSimpleTestCase(SimpleTestCase):
    def test_address_str_formatting(self) -> None:
        address = TestAddress()

        # Address string should default to United States
        self.assertEqual(str(address), "")

        address.street_address = "123 Main St."
        self.assertEqual(str(address), "123 Main St.")

        address.locality = "Anytown"
        self.assertEqual(str(address), "123 Main St., Anytown")

        address.region = "CA"
        self.assertEqual(str(address), "123 Main St., Anytown, CA")

        address.postal_code = "12345"
        self.assertEqual(str(address), "123 Main St., Anytown, CA, 12345")

        address.country = "United States"
        self.assertEqual(
            str(address),
            "123 Main St., Anytown, CA, 12345, United States",
        )
