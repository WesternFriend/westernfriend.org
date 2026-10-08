from wagtail.admin.viewsets.chooser import ChooserViewSet

from .models import Topic


class TopicChooserViewSet(ChooserViewSet):
    icon = "tag"
    model = Topic
    choose_one_text = "Choose a topic"
    choose_another_text = "Choose another topic"
    # Creating topics from this chooser needs an agreed parent in the Wagtail
    # page tree; issue #88 tracks a separate topic-selection change.


topic_chooser_viewset = TopicChooserViewSet("topic_chooser")
