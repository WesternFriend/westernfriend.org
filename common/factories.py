from typing import Any
import factory
from wagtail.models import Page


class PageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Page

    title = factory.Sequence(lambda n: f"Test Page {n}")
    slug = factory.Sequence(lambda n: f"page-{n}")

    @classmethod
    def _create(
        cls: type["PageFactory"],
        model_class: type[Page],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        instance = super()._create(model_class, *args, **kwargs)

        # Ensure the instance is added to the tree
        root = Page.get_first_root_node()
        root.add_child(instance=instance)

        return instance
