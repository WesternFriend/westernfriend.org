from wagtail.admin.viewsets.base import ViewSetGroup
from wagtail.admin.viewsets.pages import PageListingViewSet

from .models import (
    Meeting,
    Organization,
    Person,
)


class PersonViewSet(PageListingViewSet):
    model = Person
    menu_label = "People"
    name = "Person"
    icon = "user"
    add_to_settings_menu = False
    list_display = ["family_name", "given_name"]
    search_fields = ["given_name", "family_name"]
    ordering = ["family_name", "given_name"]
    list_per_page = 10


class MeetingViewSet(PageListingViewSet):
    model = Meeting
    menu_label = "Meetings"
    icon = "home"
    name = "Meeting"
    add_to_settings_menu = False
    list_display = ["title", "meeting_type"]
    search_fields = ["title"]
    ordering = ["title"]
    list_per_page = 10


class OrganizationViewSet(PageListingViewSet):
    model = Organization
    menu_label = "Organizations"
    icon = "group"
    name = "Organization"
    add_to_settings_menu = False
    list_display = ["title"]
    search_fields = ["title"]
    ordering = ["title"]
    list_per_page = 10


class ContactViewSetGroup(ViewSetGroup):
    menu_label = "Contacts"
    menu_icon = "group"
    menu_order = 100
    items = [
        PersonViewSet,
        MeetingViewSet,
        OrganizationViewSet,
    ]
