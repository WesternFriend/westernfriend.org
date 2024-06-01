from wagtail.admin.viewsets.pages import PageListingViewSet

from .models import CommunityDirectory, OnlineWorship


class CommunityDirectoryViewSet(PageListingViewSet):
    model = CommunityDirectory
    menu_label = "Directories"
    icon = "group"
    name = "directories"
    search_fields = ["title"]
    ordering = ["title"]


class OnlineWorshipViewSet(PageListingViewSet):
    model = OnlineWorship
    menu_label = "Online Worship"
    icon = "globe"
    name = "online_worship"
    search_fields = ["title"]
    ordering = ["title"]
