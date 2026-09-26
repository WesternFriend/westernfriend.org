from django.urls import re_path

from . import views

app_name = "tags"

urlpatterns = [
    re_path(
        r"^(?P<tag>[\w-]+)/$",
        views.TaggedPageListView.as_view(),
        name="tagged_page_list",
    ),
]
