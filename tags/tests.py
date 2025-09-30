import re
from django.test import TestCase
from django.urls import reverse
from taggit.models import Tag
from library.models import LibraryItem
from library.factories import LibraryItemFactory
from magazine.factories import MagazineArticleFactory
from magazine.models import MagazineArticle, MagazineArticleAuthor
from news.factories import NewsItemFactory
from news.models import NewsItem
from wf_pages.factories import WfPageFactory
from wf_pages.models import WfPage
from contact.factories import PersonFactory


class TaggedPageListViewQuerysetAndContentOrderTest(TestCase):
    def setUp(self):
        self.tag = Tag.objects.create(name="Common Tag", slug="common-tag")
        self.url = reverse("tags:tagged_page_list", kwargs={"tag": self.tag.slug})

        self.library_item = LibraryItemFactory(title="A Library Item")
        self.library_item.tags.add(self.tag)
        self.library_item.save()

        self.magazine_article = MagazineArticleFactory(title="Magazine Article")
        self.magazine_article.tags.add(self.tag)
        self.magazine_article.save()

        self.news_item = NewsItemFactory(title="News Item")
        self.news_item.tags.add(self.tag)
        self.news_item.save()

        self.wf_page = WfPageFactory(title="Wf Page")
        self.wf_page.tags.add(self.tag)
        self.wf_page.save()

    def test_setUp_data(self):
        self.assertEqual(self.tag.name, "Common Tag")
        self.assertEqual(self.tag.slug, "common-tag")
        self.assertEqual(self.library_item.title, "A Library Item")
        self.assertEqual(self.magazine_article.title, "Magazine Article")
        self.assertEqual(self.news_item.title, "News Item")
        self.assertEqual(self.wf_page.title, "Wf Page")

        library_item = LibraryItem.objects.first()
        magazine_article = MagazineArticle.objects.first()
        news_item = NewsItem.objects.first()
        wf_page = WfPage.objects.first()

        self.assertIn(self.tag, library_item.tags.all())
        self.assertIn(self.tag, magazine_article.tags.all())
        self.assertIn(self.tag, news_item.tags.all())
        self.assertIn(self.tag, wf_page.tags.all())

    def test_queryset_content_and_order(self):
        # ensure items have tags
        self.assertIn(self.tag, self.library_item.tags.all())
        self.assertIn(self.tag, self.magazine_article.tags.all())
        self.assertIn(self.tag, self.news_item.tags.all())
        self.assertIn(self.tag, self.wf_page.tags.all())

        response = self.client.get(self.url)
        paginated_context = response.context["paginated_items"]

        # Access the items in the paginated page
        queryset_items = paginated_context.page.object_list

        # expected four items
        self.assertEqual(len(queryset_items), 4)

        # Expected items in alphabetical order by title
        expected_titles = sorted(
            [
                self.library_item.title,
                self.magazine_article.title,
                self.news_item.title,
                self.wf_page.title,
            ],
        )

        # Extract titles from the queryset items
        actual_titles = [item.title for item in queryset_items]

        # Check if all expected items are in the queryset
        self.assertListEqual(expected_titles, actual_titles)

        # Verify the sorting order by title
        self.assertEqual(expected_titles, actual_titles)


class TaggedPageListViewPaginationTest(TestCase):
    def setUp(self):
        self.tag = Tag.objects.create(name="Common Tag", slug="common-tag")
        self.url = reverse("tags:tagged_page_list", kwargs={"tag": self.tag.slug})

        # pagination requires at least ten items
        # create N items for each model
        # where N * 4 >= 10
        N = 3

        for i in range(N):
            library_item = LibraryItemFactory(title=f"Library Item {i}")
            library_item.tags.add(self.tag)
            library_item.save()

            magazine_article = MagazineArticleFactory(title=f"Magazine Article {i}")
            magazine_article.tags.add(self.tag)
            magazine_article.save()

            news_item = NewsItemFactory(title=f"News Item {i}")
            news_item.tags.add(self.tag)
            news_item.save()

            wf_page = WfPageFactory(title=f"Wf Page {i}")
            wf_page.tags.add(self.tag)
            wf_page.save()

    def test_pagination(self):
        response = self.client.get(self.url)
        paginated_context = response.context["paginated_items"]

        queryset_items = paginated_context.page.object_list

        expected_items = 10
        self.assertEqual(len(queryset_items), expected_items)

        expected_pages_count = 2
        self.assertEqual(
            paginated_context.page.paginator.num_pages,
            expected_pages_count,
        )

        expected_page_number = 1
        self.assertEqual(paginated_context.page.number, expected_page_number)

        expected_next_page = 2
        self.assertEqual(paginated_context.page.next_page_number(), expected_next_page)

    def test_pagination_second_page(self):
        response = self.client.get(self.url + "?page=2")
        paginated_context = response.context["paginated_items"]

        queryset_items = paginated_context.page.object_list

        expected_items = 2
        self.assertEqual(len(queryset_items), expected_items)

        expected_pages_count = 2
        self.assertEqual(
            paginated_context.page.paginator.num_pages,
            expected_pages_count,
        )

        expected_page_number = 2
        self.assertEqual(paginated_context.page.number, expected_page_number)

        expected_previous_page = 1
        self.assertEqual(
            paginated_context.page.previous_page_number(),
            expected_previous_page,
        )


class TaggedPageListViewTemplateRenderingTest(TestCase):
    def setUp(self):
        self.tag = Tag.objects.create(name="Authors Tag", slug="authors-tag")
        self.url = reverse("tags:tagged_page_list", kwargs={"tag": self.tag.slug})

        # Create a magazine article and attach authors
        self.article = MagazineArticleFactory(title="Article With Authors")
        self.article.tags.add(self.tag)
        self.article.save()

        self.person_live = PersonFactory()
        # Publish person_live so template renders it as a link
        self.person_live.save_revision().publish()

        self.person_not_live = PersonFactory()
        # Ensure non-live stays unpublished for template logic
        self.person_not_live.live = False
        self.person_not_live.save()

        MagazineArticleAuthor.objects.create(
            article=self.article,
            author=self.person_live,
        )
        MagazineArticleAuthor.objects.create(
            article=self.article,
            author=self.person_not_live,
        )

    def test_authors_and_issue_render_with_accessible_markup(self):
        response = self.client.get(self.url)
        html = response.content.decode()

        # Authors label and list present with dynamic id
        self.assertIn("Authors", html)
        # Extract actual authors-label id from the span
        m = re.search(
            r"<span[^>]*id=\"(authors-label-[^\"]+)\"[^>]*>\s*Authors\s*:</span>",
            html,
        )
        self.assertIsNotNone(m, "Could not find authors label span with id")
        label_id = m.group(1)
        # Verify aria-labelledby matches the extracted id
        self.assertIn(f'aria-labelledby="{label_id}"', html)

        # Live author should be linked
        live_title = self.person_live.title
        self.assertRegex(html, rf"<a[^>]*>\s*{re.escape(live_title)}\s*</a>")
        # Non-live author should be plain text (no anchor)
        non_live_title = self.person_not_live.title
        self.assertIn(non_live_title, html)
        self.assertIsNone(
            re.search(rf"<a[^>]*>\s*{re.escape(non_live_title)}\s*</a>", html),
        )

        # Issue label and machine-readable date present
        self.assertIn("Issue", html)
        expected_date = self.article.get_parent().specific.publication_date.strftime(
            "%Y-%m-%d",
        )
        self.assertIn(f'<time datetime="{expected_date}"', html)
