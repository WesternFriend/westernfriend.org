from typing import Any
import factory
from factory.django import DjangoModelFactory
from django.utils.text import slugify
from wagtail.models import Page


from home.models import HomePage


class HomePageFactory(DjangoModelFactory):
    class Meta:
        model = HomePage

    title = factory.Faker("sentence", nb_words=4)  # type: ignore
    slug = factory.LazyAttribute(lambda obj: slugify(obj.title))  # type: ignore
    depth = factory.Sequence(lambda n: n + 2)  # Assumes that root page depth is 1

    @factory.lazy_attribute  # type: ignore
    def path(self):
        # Constructs a valid path by appending self.depth
        # to the path of root page
        root_path = Page.get_first_root_node().path
        return f"{root_path}{str(self.depth).zfill(4)}"

    @factory.post_generation
    def add_to_root_page(
        self,
        create: bool,
        extracted: Any,
        **kwargs: Any,
    ) -> None:
        if not create:
            return
        root_page = Page.get_first_root_node()

        if not HomePage.objects.exists():
            root_page.add_child(instance=self)
