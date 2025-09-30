import factory
from wagtail_factories import PageFactory

from navigation.blocks import NavigationExternalLinkBlock, NavigationPageChooserBlock


class NavigationExternalLinkBlockFactory(factory.Factory):
    class Meta:
        model = NavigationExternalLinkBlock

    title = factory.Faker("sentence", nb_words=4)  # type: ignore
    url = factory.Faker("url")  # type: ignore
    anchor = factory.Faker("word")  # type: ignore


class NavigationPageChooserBlockFactory(factory.Factory):
    class Meta:
        model = NavigationPageChooserBlock

    title = factory.Faker("sentence")
    page = factory.SubFactory(PageFactory)
    anchor = factory.Faker("word")
