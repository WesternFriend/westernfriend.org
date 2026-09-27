from random import randint
from typing import Any

import factory
from django.utils.text import slugify
from factory.django import DjangoModelFactory
from wagtail.models import Page

from common.fake_content import (
    EMAIL_DOMAIN,
    ORGANIZATION_KINDS,
    TOPICS,
    YEARLY_MEETING_REGIONS,
    fake,
    paragraphs,
)
from community.factories import CommunityPageFactory
from community.models import CommunityPage

from .models import (
    Meeting,
    MeetingAddress,
    MeetingIndexPage,
    MeetingPresidingClerk,
    MeetingWorshipTime,
    Organization,
    OrganizationIndexPage,
    Person,
    PersonIndexPage,
    WorshipTypeChoices,
)


class PersonIndexPageFactory(DjangoModelFactory):
    class Meta:
        model = PersonIndexPage

    title = factory.Faker("sentence", nb_words=4)  # type: ignore
    slug = factory.LazyAttribute(lambda obj: slugify(obj.title))  # type: ignore

    @classmethod
    def _create(
        cls: type["PersonIndexPageFactory"],
        model_class: type[Page],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        instance = model_class(*args, **kwargs)
        parent = CommunityPage.objects.first()
        if parent:
            parent.add_child(instance=instance)
        else:
            community_page = CommunityPageFactory.create()
            community_page.add_child(instance=instance)
        return instance


class PersonFactory(DjangoModelFactory):
    class Meta:
        model = Person

    class Params:
        # Most people in the directory list some way to reach them.
        has_contact_details = factory.Faker("boolean", chance_of_getting_true=60)

    given_name: str = factory.Faker("first_name")  # type: ignore
    family_name: str = factory.Faker("last_name")  # type: ignore
    email = factory.Maybe(  # type: ignore
        "has_contact_details",
        yes_declaration=factory.Faker("email", domain=EMAIL_DOMAIN),
        no_declaration="",
    )
    phone = factory.Maybe(  # type: ignore
        "has_contact_details",
        yes_declaration=factory.Faker("phone_number"),
        no_declaration="",
    )
    website = factory.Maybe(  # type: ignore
        factory.Faker("boolean", chance_of_getting_true=20),
        yes_declaration=factory.Faker("url"),
        no_declaration="",
    )

    @factory.lazy_attribute  # type: ignore
    def title(self) -> str:
        return f"{self.given_name} {self.family_name}"

    @factory.lazy_attribute  # type: ignore
    def slug(self) -> str:
        random_number = randint(1, 1000)
        return f"{self.given_name}-{self.family_name}-{random_number}".lower()

    @classmethod
    def _create(
        cls: type["PersonFactory"],
        model_class: type[Page],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        instance = model_class(*args, **kwargs)
        parent = PersonIndexPage.objects.first()
        if parent:
            parent.add_child(instance=instance)
        else:
            community_page = PersonIndexPageFactory.create()
            community_page.add_child(instance=instance)
        return instance


class MeetingIndexPageFactory(DjangoModelFactory):
    class Meta:
        model = MeetingIndexPage

    title = factory.Faker("sentence", nb_words=4)  # type: ignore
    slug = factory.LazyAttribute(lambda obj: slugify(obj.title))  # type: ignore

    @classmethod
    def _create(
        cls: type["MeetingIndexPageFactory"],
        model_class: type[Page],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        instance = model_class(*args, **kwargs)
        parent = CommunityPage.objects.first()
        if parent:
            parent.add_child(instance=instance)
        else:
            community_page = CommunityPageFactory.create()
            community_page.add_child(instance=instance)
        return instance


def _add_meeting_details(meeting: Meeting, create: bool, extracted: Any) -> None:
    """Give a meeting worship times and, usually, worship and mailing addresses."""
    meeting.worship_times = MeetingWorshipTimeFactory.build_batch(
        fake.random_int(1, 3),
    )
    if meeting.meeting_type != Meeting.MeetingTypeChoices.YEARLY_MEETING:
        # Some meetings have no address, so templates must handle the gap.
        address_count = fake.random_element([0, 1, 1, 2, 2, 2])
        meeting.addresses = [
            MeetingAddressFactory.build(),
            MeetingAddressFactory.build(mailing=True),
        ][:address_count]
    if create:
        meeting.save()


class MeetingFactory(DjangoModelFactory):
    class Meta:
        model = Meeting

    class Params:
        yearly_meeting = factory.Trait(
            meeting_type=Meeting.MeetingTypeChoices.YEARLY_MEETING,
            title=factory.LazyFunction(
                lambda: f"{fake.random_element(YEARLY_MEETING_REGIONS)} Yearly Meeting",
            ),
        )
        quarterly_meeting = factory.Trait(
            meeting_type=Meeting.MeetingTypeChoices.QUARTERLY_MEETING,
            title=factory.LazyFunction(lambda: f"{fake.city()} Quarterly Meeting"),
        )
        monthly_meeting = factory.Trait(
            meeting_type=Meeting.MeetingTypeChoices.MONTHLY_MEETING,
            title=factory.LazyFunction(lambda: f"{fake.city()} Friends Meeting"),
        )
        worship_group = factory.Trait(
            meeting_type=Meeting.MeetingTypeChoices.WORSHIP_GROUP,
            title=factory.LazyFunction(lambda: f"{fake.city()} Worship Group"),
        )
        # Fill every optional field and add worship times and addresses.
        complete = factory.Trait(
            description=factory.LazyFunction(paragraphs),
            website=factory.Faker("url"),
            email=factory.Faker("email", domain=EMAIL_DOMAIN),
            phone=factory.Faker("phone_number"),
            information_last_verified=factory.Faker("date_between", start_date="-2y"),
            details=factory.PostGeneration(_add_meeting_details),
        )

    title = factory.sequence(lambda n: f"Meeting {n}")  # type: ignore
    slug = factory.Sequence(lambda n: f"meeting-{n}")  # type: ignore
    details = factory.PostGeneration(lambda *_args, **_kwargs: None)  # type: ignore

    @classmethod
    def _create(
        cls,
        model_class: type[Meeting],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        instance = model_class(*args, **kwargs)  # type: ignore
        parent = MeetingIndexPage.objects.first()
        if parent:
            parent.add_child(instance=instance)
        else:
            community_page = MeetingIndexPageFactory.create()
            community_page.add_child(instance=instance)
        return instance


class OrganizationIndexPageFactory(DjangoModelFactory):
    class Meta:
        model = OrganizationIndexPage

    title = factory.Sequence(lambda n: f"Organization {n}")  # type: ignore
    slug = factory.LazyAttribute(lambda obj: slugify(obj.title))  # type: ignore

    @classmethod
    def _create(
        cls: type["OrganizationIndexPageFactory"],
        model_class: type[Page],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        instance = model_class(*args, **kwargs)
        parent = CommunityPage.objects.first()
        if parent:
            parent.add_child(instance=instance)
        else:
            community_page = CommunityPageFactory.create()
            community_page.add_child(instance=instance)
        return instance


class OrganizationFactory(DjangoModelFactory):
    class Meta:
        model = Organization

    title = factory.LazyFunction(  # type: ignore
        lambda: (
            f"Friends {fake.random_element(ORGANIZATION_KINDS)} "
            f"for {fake.random_element(TOPICS)}"
        ),
    )
    slug = factory.Sequence(lambda n: f"organization-{n}")  # type: ignore
    description = factory.Faker("sentence", nb_words=12)  # type: ignore
    website = factory.Faker("url")  # type: ignore
    email = factory.Faker("email", domain=EMAIL_DOMAIN)  # type: ignore
    phone = factory.Faker("phone_number")  # type: ignore

    @classmethod
    def _create(
        cls,
        model_class: type[Organization],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        instance = model_class(*args, **kwargs)  # type: ignore
        parent = OrganizationIndexPage.objects.first()
        if parent:
            parent.add_child(instance=instance)
        else:
            community_page = OrganizationIndexPageFactory.create()
            community_page.add_child(instance=instance)
        return instance


class MeetingPresidingClerkFactory(DjangoModelFactory):
    """Presiding clerk; pass ``person=`` and attach via the meeting's cluster."""

    class Meta:
        model = MeetingPresidingClerk


class MeetingWorshipTimeFactory(DjangoModelFactory):
    """Worship time for a Meeting; pass ``meeting=`` or attach via the cluster."""

    class Meta:
        model = MeetingWorshipTime

    worship_type = factory.Faker(  # type: ignore
        "random_element",
        elements=WorshipTypeChoices.values,
    )
    worship_time = factory.Faker(  # type: ignore
        "random_element",
        elements=[
            "Sundays at 10:00 a.m.",
            "Sundays at 10:30 a.m.",
            "First Sundays at 12:00 p.m.",
            "Wednesdays at 7:00 p.m.",
            "Second Sundays after worship",
        ],
    )


class MeetingAddressFactory(DjangoModelFactory):
    """Address for a Meeting; pass ``page=`` or attach via the cluster."""

    class Meta:
        model = MeetingAddress

    class Params:
        # A post office box without map coordinates.
        mailing = factory.Trait(
            address_type=MeetingAddress.AddressTypeChoices.MAILING,
            street_address="",
            po_box_number=factory.Faker("numerify", text="####"),
            latitude=None,
            longitude=None,
        )

    address_type = MeetingAddress.AddressTypeChoices.WORSHIP
    street_address = factory.Faker("street_address")  # type: ignore
    locality = factory.Faker("city")  # type: ignore
    region = factory.Faker("state_abbr")  # type: ignore
    postal_code = factory.Faker("zipcode")  # type: ignore
    country = "United States"
    latitude = factory.Faker("pyfloat", min_value=32, max_value=48)  # type: ignore
    longitude = factory.Faker("pyfloat", min_value=-124, max_value=-104)  # type: ignore
