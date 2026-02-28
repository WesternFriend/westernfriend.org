from itertools import chain

from django.views.generic import ListView
from django.db.models import Q
from taggit.models import Tag
from wagtail.admin.viewsets.model import ModelViewSet
from wagtail.models import Page

from library.models import LibraryItem
from magazine.models import MagazineArticle, MagazineIssue
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

        library_items = (
            LibraryItem.get_queryset()
            .filter(filter_condition)
            .live()
            .public()
            .select_related("content_type")
            .prefetch_related("authors__author")
            # DB-level ordering unnecessary; combined list is sorted below
        )

        magazine_articles = list(
            MagazineArticle.get_queryset()
            .filter(filter_condition)
            .live()
            .public()
            .select_related("content_type")
            .prefetch_related("authors__author"),
            # DB-level ordering unnecessary; combined list is sorted below
        )

        # Prefetch parent MagazineIssues in bulk to avoid N+1 from
        # article.get_parent().specific in magazine_article_summary.html
        if magazine_articles:
            step_len = Page.steplen
            parent_paths = {a.path[:-step_len] for a in magazine_articles}
            parent_issues_by_path = {
                issue.path: issue
                for issue in MagazineIssue.objects.filter(path__in=parent_paths)
            }
            for article in magazine_articles:
                parent = parent_issues_by_path.get(article.path[:-step_len])
                if parent is not None:
                    article._parent_page_cache = parent

        news_items = (
            NewsItem.objects.filter(filter_condition)
            .live()
            .public()
            .select_related("content_type")
            # DB-level ordering unnecessary; combined list is sorted below
        )

        pages = (
            WfPage.get_queryset()
            .filter(filter_condition)
            .live()
            .public()
            .select_related("content_type")
            # DB-level ordering unnecessary; combined list is sorted below
        )

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


class TagViewSet(ModelViewSet):
    model = Tag
    menu_label = "Tags"
    icon = "tag"
    name = "content_tags"
    list_display = (
        "name",
        "slug",
    )
    search_fields = ("name",)
    ordering = ["name"]
    form_fields = [
        "name",
        "slug",
    ]
