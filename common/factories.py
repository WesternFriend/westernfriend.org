from typing import Any
import factory
from wagtail.models import Page


class PageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Page

    title = factory.Sequence(lambda n: f"Test Page {n}")

    @factory.post_generation
    def add_to_root(
        obj: "PageFactory",
        create: bool,
        extracted: Any | None,
        **kwargs: Any,
    ) -> None:
        if create:
            root_page = Page.objects.first()
            root_page.add_child(instance=obj)
            obj.save()
