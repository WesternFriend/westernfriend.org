from wagtail.admin.viewsets.pages import PageListingViewSet

from .models import CommunityDirectory


class CommunityDirectoryViewSet(PageListingViewSet):
    model = CommunityDirectory
    menu_label = "Directories"
    icon = "group"
    name = "directories"
    search_fields = ["title"]
    ordering = ["title"]
