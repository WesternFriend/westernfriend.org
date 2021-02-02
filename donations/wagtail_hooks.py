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
        "recurrence",
        "paid",
    )
    inspect_view_enabled = True
    inspect_view_fields = [
        "donor_given_name",
        "donor_family_name",
        "donor_email",
        "donor_address",
        "amount",
        "paid",
        "braintree_transaction_id",
        "braintree_subscription_id",
    ]
    search_fields = (
        "donor_given_name",
        "donor_family_name",
        "donor_email",
    )
    list_filter = (
        "paid",
        "recurrence",
    )
    list_export = (
        "donor_given_name",
        "donor_family_name",
        "donor_email",
        "donor_address",
        "amount",
        "paid",
        "braintree_transaction_id",
        "braintree_subscription_id",
    )


modeladmin_register(DonationModelAdmin)
