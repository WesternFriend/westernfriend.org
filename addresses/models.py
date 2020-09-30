from django.db import models

from wagtail.admin.edit_handlers import FieldPanel

ADDRESS_TYPE_CHOICES = (("mailing", "mailing"), ("worship", "worship"))


class Address(models.Model):
    """
    Model representing a street or post office address.

    Properties are modelled after Microformats specification.
    http://microformats.org/wiki/adr
    """

    street_address = models.CharField(max_length=255, blank=True, default="",)
    extended_address = models.CharField(max_length=255, blank=True, default="",)
    po_box_number = models.CharField(
        max_length=32, blank=True, default="", help_text="P.O. Box, if relevant."
    )
    locality = models.CharField(
        max_length=255, help_text="City for the shipping address."
    )
    region = models.CharField(
        max_length=255, help_text="State or region.", blank=True, default=""
    )
    postal_code = models.CharField(max_length=16, help_text="Postal code (or zipcode).")
    country = models.CharField(
        max_length=255, default="United States", help_text="Country for shipping."
    )
    address_type = models.CharField(max_length=255, choices=ADDRESS_TYPE_CHOICES)

    panels = [
        FieldPanel("street_address"),
        FieldPanel("extended_address"),
        FieldPanel("po_box_number"),
        FieldPanel("locality"),
        FieldPanel("region"),
        FieldPanel("postal_code"),
        FieldPanel("country"),
    ]

    def __str__(self):
        return f"{self.street_address}, {self.locality}, {self.region} {self.country}"

    class Meta:
        abstract = True
