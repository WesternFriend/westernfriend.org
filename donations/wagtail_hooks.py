from wagtail.contrib.modeladmin.options import (
    ModelAdmin,
    modeladmin_register
)

from donations.models import Donation


class DonationModelAdmin(ModelAdmin):
    """Donation admin."""

    model = Donation
    menu_label = "Donations"
    menu_icon = "fa-gift"
    menu_order = 291
    add_to_settings_menu = False
    exclude_from_explorer = True
    list_display = (
        "donor_given_name",
        "donor_family_name",
        "donor_email",
        "amount",
        "paid",
    )
    inspect_view_enabled = True
    inspect_view_fields = [
        "donor_given_name",
        "donor_family_name",
        "donor_email",
        "amount",
        "paid",
    ]
    search_fields = (
        "donor_given_name",
        "donor_family_name",
        "donor_email",
    )


modeladmin_register(DonationModelAdmin)
