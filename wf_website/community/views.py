from django.views.generic import ListView
from contact.models import Organization


class QuakerOrganizationList(ListView):
    model = Organization
    context_object_name = "organizations"
    template_name = "community/quaker_organization_list.html"
