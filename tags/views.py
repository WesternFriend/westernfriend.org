from itertools import chain

from django.views.generic import ListView
from django.db.models import Q
from taggit.models import Tag

from library.models import LibraryItem
from magazine.models import MagazineArticle
from news.models import NewsItem
from pagination.helpers import get_paginated_items
from wf_pages.models import WfPage


class TaggedPageListView(ListView):
    template_name = "tags/tagged_page_list.html"
    paginate_by = 10

    def get_queryset(self):
        """Return a list of all the pages tagged with the given tag.

        The combined list is sorted alphabetically by title.
        """
        tag = self.kwargs["tag"]
        # Get all the pages tagged with the given tag
        filter_condition = Q(tags__slug__in=[tag])

        library_items = LibraryItem.objects.filter(filter_condition).order_by("title")

        magazine_articles = MagazineArticle.objects.filter(filter_condition).order_by(
            "title",
        )

        news_items = NewsItem.objects.filter(filter_condition).order_by("title")

        pages = WfPage.objects.filter(filter_condition).order_by("title")

        combined_queryset_list = list(
            chain(
                library_items,
                magazine_articles,
                news_items,
                pages,
            ),
        )

        sorted_queryset = sorted(
            combined_queryset_list,
            key=lambda instance: instance.title.lower(),
        )

        return sorted_queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        tag_slug = self.kwargs["tag"]
        tag_name = Tag.objects.get(slug=tag_slug).name

        context["tag_name"] = tag_name

        page_number = self.request.GET.get("page", "1")

        context["paginated_items"] = get_paginated_items(
            items=self.get_queryset(),
            items_per_page=self.paginate_by,
            page_number=page_number,
        )

        return context
