from wagtail import hooks
from .views import news_item_viewset


@hooks.register("register_admin_viewset")
def register_news_item_viewset():
    return news_item_viewset
