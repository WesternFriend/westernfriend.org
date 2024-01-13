from typing import Any
import factory

from home.models import HomePage

from .models import WfPage


class WfPageFactory(
    factory.django.DjangoModelFactory,
):
    class Meta:
        model = WfPage

    title = factory.Faker("sentence", nb_words=4)  # type: ignore
    # slug = factory.LazyAttribute(lambda obj: slugify(obj.title))  # type: ignore

    @classmethod
    def _create(
        cls,
        model_class: type[WfPage],
        *args: Any,
        **kwargs: Any,
    ) -> WfPage:
        instance = model_class(*args, **kwargs)  # type: ignore
        parent = HomePage.objects.first()
        if parent:
            parent.add_child(instance=instance)
        else:
            home_page = WfPageFactory.create()
            home_page.add_child(instance=instance)
        return instance
