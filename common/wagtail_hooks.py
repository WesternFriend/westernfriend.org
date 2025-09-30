from wagtail import hooks
from .views import (
    ContentViewSetGroup,
)


@hooks.register("register_admin_viewset")
def register_content_viewset_group():
    return ContentViewSetGroup()
