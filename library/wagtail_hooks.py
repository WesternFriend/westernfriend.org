from wagtail import hooks
from library.views import LibraryViewSetGroup


@hooks.register("register_admin_viewset")
def register_magazine_viewset_group():
    return LibraryViewSetGroup()
