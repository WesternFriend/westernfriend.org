from django.db import models

from wagtail.core.models import Page


class FacetIndexPage(Page):
    parent_page_types = ["library.LibraryIndexPage"]
    subpage_types = [
        "AudienceIndexPage",
        "GenreIndexPage",
        "MediumIndexPage",
        "TimePeriodIndexPage",
        "TopicIndexPage",
    ]

    max_count = 1


class AudienceIndexPage(Page):
    parent_page_types = ["FacetIndexPage"]
    subpage_types = ["Audience"]

    max_count = 1


class Audience(Page):
    parent_page_types = ["AudienceIndexPage"]
    subpage_types = []


class GenreIndexPage(Page):
    parent_page_types = ["FacetIndexPage"]
    subpage_types = ["Genre"]

    max_count = 1


class Genre(Page):
    parent_page_types = ["GenreIndexPage"]
    subpage_types = []


class MediumIndexPage(Page):
    parent_page_types = ["FacetIndexPage"]
    subpage_types = ["Medium"]

    max_count = 1


class Medium(Page):
    parent_page_types = ["MediumIndexPage"]
    subpage_types = []


class TimePeriodIndexPage(Page):
    parent_page_types = ["FacetIndexPage"]
    subpage_types = ["TimePeriod"]

    max_count = 1


class TimePeriod(Page):
    parent_page_types = ["TimePeriodIndexPage"]
    subpage_types = []


class TopicIndexPage(Page):
    parent_page_types = ["FacetIndexPage"]
    subpage_types = ["Topic"]

    max_count = 1


class Topic(Page):
    parent_page_types = ["TopicIndexPage"]
    subpage_types = []
