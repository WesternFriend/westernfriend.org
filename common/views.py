from http import HTTPStatus
from django.shortcuts import render
from wagtail.admin.viewsets.base import ViewSetGroup

from community.views import CommunityDirectoryViewSet, OnlineWorshipViewSet
from documents.views import MeetingDocumentViewSet, PublicBoardDocumentViewSet
from events.views import EventViewSet
from wf_pages.views import MollyWingateBlogPageViewSet


class ContentViewSetGroup(ViewSetGroup):
    menu_label = "Content"
    menu_icon = "snippet"
    menu_order = 101
    items = [
        CommunityDirectoryViewSet,
        EventViewSet,
        OnlineWorshipViewSet,
        MeetingDocumentViewSet,
        PublicBoardDocumentViewSet,
        MollyWingateBlogPageViewSet,
    ]


def custom_404(request, exception=None):  # noqa: W0613 # skipcq: PYL-W0613
    """Return the 404 page with search form that will contain the URL path
    components that the user requested. The path will be split into the
    keywords and the keywords will be used to populate the search field.

    E.g., westernfriend.org/some-missing-page/with-subpage will return
    the 404 page with the search field populated with "some missing page
    with subpage".
    """
    context = {}

    # Get the path from the request
    path = request.path

    # Split the requested path to form a search query
    # e.g. /page-not-found/ -> page not found
    search_query = path.replace("-", " ").replace("/", " ").strip()

    # Add the custom variable to the context dictionary
    context["search_query"] = search_query

    # Render the 404 page with the custom variable
    return render(
        request,
        "404.html",
        context=context,
        status=HTTPStatus.NOT_FOUND,
    )
