from wagtail import hooks
from .views import (
    MagazineViewSetGroup,
)


@hooks.register("register_admin_viewset")
def register_magazine_viewset_group():
    return MagazineViewSetGroup()
