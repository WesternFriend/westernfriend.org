from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register
from .models import Address

@modeladmin_register
class AddressModelAdmin(ModelAdmin):
    model = Address
    list_display = (
        'street_address',
    )
    search_fields = (
        'street_address',
    )
