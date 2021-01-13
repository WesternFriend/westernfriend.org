from django.db import models

from wagtail.admin.edit_handlers import FieldPanel

ADDRESS_TYPE_CHOICES = (("mailing", "Mailing"), ("worship", "Worship"))


class Address(models.Model):
    """
    Model representing a street or post office address.

    Properties are modelled after Microformats specification.
    http://microformats.org/wiki/adr
    """

    street_address = models.CharField(max_length=255, blank=True, default="",)
    extended_address = models.CharField(max_length=255, blank=True, default="",)
    po_box_number = models.CharField(
        max_length=32, blank=True, default="", help_text="P.O. Box, if relevant"
    )
    locality = models.CharField(max_length=255, help_text="Locality or city", null=True, blank=True)
    region = models.CharField(
        max_length=255, help_text="State or region", blank=True, default=""
    )
    postal_code = models.CharField(max_length=16, help_text="Postal code (or zipcode)", null=True, blank=True)
    country = models.CharField(max_length=255, default="United States", null=True, blank=True)
    address_type = models.CharField(max_length=255, choices=ADDRESS_TYPE_CHOICES)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    panels = [
        FieldPanel("address_type"),
        FieldPanel("street_address"),
        FieldPanel("extended_address"),
        FieldPanel("po_box_number"),
        FieldPanel("locality"),
        FieldPanel("region"),
        FieldPanel("postal_code"),
        FieldPanel("country"),
        FieldPanel("latitude"),
        FieldPanel("longitude"),
    ]

    def __str__(self):
        return f"{self.street_address}, {self.locality}, {self.region} {self.country}"

    class Meta:
        abstract = True
