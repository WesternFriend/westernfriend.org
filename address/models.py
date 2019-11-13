from django.db import models

class Address(models.Model):
    street_address = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )
    postal_code = models.CharField(
        max_length=16,
    )
    po_box_number = models.CharField(
        max_length=32, blank=True, default=""
    )
    address_locality = models.CharField(
        max_length=255
    )
    address_region = models.CharField(
        max_length=255, blank=True, default=""
    )
    address_country = models.CharField(
        max_length=255, default="United States"
    )
    