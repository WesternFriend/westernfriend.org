from wagtail import hooks
from .views import StoreViewSetGroup


@hooks.register("register_admin_viewset")
def register_store_viewset():
    return StoreViewSetGroup()
