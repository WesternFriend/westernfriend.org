import factory

from navigation.blocks import (
    NavigationExternalLinkBlock,
)


class NavigationExternalLinkBlockFactory(factory.Factory):
    class Meta:
        model = NavigationExternalLinkBlock

    title = factory.Faker("sentence", nb_words=4)  # type: ignore
    url = factory.Faker("url")  # type: ignore
    anchor = factory.Faker("word")  # type: ignore
