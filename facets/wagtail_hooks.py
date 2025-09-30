from wagtail import hooks

from .views import topic_chooser_viewset


@hooks.register("register_admin_viewset")
def register_topic_chooser_viewset():
    return topic_chooser_viewset
