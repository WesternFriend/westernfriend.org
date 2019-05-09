from django.views.generic import ListView
from contact.models import Contact


class QuakerOrganizationList(ListView):
    model = Contact
    context_object_name = "organizations"
    template_name = "community/quaker_organization_list.html"

    def get_queryset(self):
        queryset = super().get_queryset()

        return queryset.filter(contact_type="quaker_organization")
