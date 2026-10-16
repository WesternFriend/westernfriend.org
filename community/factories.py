import datetime
from typing import Any

import factory
from django.utils.text import slugify
from factory.django import DjangoModelFactory

from common.fake_content import (
    WESTERN_TIMEZONES,
    YEARLY_MEETING_REGIONS,
    fake,
    paragraphs,
)
from community.models import (
    CommunityDirectory,
    CommunityDirectoryIndexPage,
    CommunityPage,
    OnlineWorship,
    OnlineWorshipIndexPage,
)
from home.factories import HomePageFactory
from home.models import HomePage


class CommunityPageFactory(DjangoModelFactory):
    class Meta:
        model = CommunityPage

    title = factory.Faker("sentence", nb_words=4)  # type: ignore
    slug = factory.LazyAttribute(lambda obj: slugify(obj.title))  # type: ignore

    @classmethod
    def _create(
        cls,
        model_class: type[CommunityPage],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        instance = model_class(*args, **kwargs)  # type: ignore
        parent = HomePage.objects.first()
        if parent:
            parent.add_child(instance=instance)
        else:
            home_page = HomePageFactory.create()
            home_page.add_child(instance=instance)
        return instance


class OnlineWorshipIndexPageFactory(DjangoModelFactory):
    class Meta:
        model = OnlineWorshipIndexPage

    title = factory.Faker("sentence", nb_words=4)  # type: ignore
    slug = factory.LazyAttribute(lambda obj: slugify(obj.title))  # type: ignore

    @classmethod
    def _create(
        cls,
        model_class: type[OnlineWorshipIndexPage],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        instance = model_class(*args, **kwargs)  # type: ignore
        parent = CommunityPage.objects.first()
        if parent:
            parent.add_child(instance=instance)
        else:
            community_page = CommunityPageFactory.create()
            community_page.add_child(instance=instance)
        return instance


class OnlineWorshipFactory(DjangoModelFactory):
    class Meta:
        model = OnlineWorship

    title = factory.Sequence(lambda n: f"Online Worship {n}")  # type: ignore
    slug = factory.LazyAttribute(lambda obj: slugify(obj.title))  # type: ignore
    description = factory.LazyFunction(paragraphs)  # type: ignore
    online_worship_day = factory.Faker(  # type: ignore
        "random_element",
        elements=OnlineWorship.OnlineWorshipDayChoices.values,
    )
    online_worship_time = factory.LazyFunction(  # type: ignore
        lambda: datetime.time(fake.random_int(7, 19), fake.random_element([0, 30])),
    )
    online_worship_timezone = factory.Faker(  # type: ignore
        "random_element",
        elements=WESTERN_TIMEZONES,
    )
    times_of_worship = factory.LazyAttribute(  # type: ignore
        lambda obj: (
            f"<p>{obj.online_worship_day}s at "
            # %-I drops the leading zero on glibc but raises ValueError on
            # Windows, so work the 12-hour clock out in Python instead.
            f"{obj.online_worship_time.hour % 12 or 12}:"
            f"{obj.online_worship_time:%M %p} ({obj.online_worship_timezone})</p>"
        ),
    )
    website = factory.Faker("url")  # type: ignore

    @classmethod
    def _create(
        cls,
        model_class: type[OnlineWorship],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        instance = model_class(*args, **kwargs)  # type: ignore
        parent = OnlineWorshipIndexPage.objects.first()
        if parent:
            parent.add_child(instance=instance)
        else:
            online_worship_index_page = OnlineWorshipIndexPageFactory.create()
            online_worship_index_page.add_child(instance=instance)
        return instance


class CommunityDirectoryIndexPageFactory(DjangoModelFactory):
    class Meta:
        model = CommunityDirectoryIndexPage

    title = factory.Sequence(lambda n: f"Community directories {n}")  # type: ignore

    @classmethod
    def _create(
        cls,
        model_class: type[CommunityDirectoryIndexPage],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        instance = model_class(*args, **kwargs)  # type: ignore
        parent = CommunityPage.objects.first() or CommunityPageFactory.create()
        parent.add_child(instance=instance)
        return instance


class CommunityDirectoryFactory(DjangoModelFactory):
    class Meta:
        model = CommunityDirectory

    title = factory.LazyFunction(  # type: ignore
        lambda: (
            f"{fake.random_element(YEARLY_MEETING_REGIONS)} "
            f"{fake.random_element(['Friends Directory', 'Meeting Directory', 'Resource Guide'])}"
        ),
    )
    slug = factory.Sequence(lambda n: f"directory-{n}")  # type: ignore
    description = factory.LazyFunction(paragraphs)  # type: ignore
    website = factory.Faker("url")  # type: ignore

    @classmethod
    def _create(
        cls,
        model_class: type[CommunityDirectory],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        instance = model_class(*args, **kwargs)  # type: ignore
        parent = CommunityDirectoryIndexPage.objects.first()
        if parent:
            parent.add_child(instance=instance)
        else:
            directory_index_page = CommunityDirectoryIndexPageFactory.create()
            directory_index_page.add_child(instance=instance)
        return instance
