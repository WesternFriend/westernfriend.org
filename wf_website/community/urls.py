from django.urls import path
from community.views import QuakerOrganizationList

urlpatterns = [
    path(
        "quaker-organizations/",
        QuakerOrganizationList.as_view(),
        name="quaker_organizations"
    ),
]
