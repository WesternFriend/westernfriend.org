from wagtail.admin.viewsets.chooser import ChooserViewSet

from .models import Topic


class TopicChooserViewSet(ChooserViewSet):
    icon = "tag"
    model = Topic
    choose_one_text = "Choose a topic"
    choose_another_text = "Choose another topic"
    # TODO: determine how to enable editing/creation of topics
    # which is made difficult since they are pages,
    # so need to be placed into the Wagtail page tree
    # edit_item_text = "Edit topic"
    # form_fields = ["title"]


topic_chooser_viewset = TopicChooserViewSet("topic_chooser")
