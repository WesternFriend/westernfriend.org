from django.urls import path
from . import views


app_name = "tags"

urlpatterns = [
    path(
        "<slug:tag>/",
        views.TaggedPageListView.as_view(),
        name="tagged_page_list",
    ),
]
