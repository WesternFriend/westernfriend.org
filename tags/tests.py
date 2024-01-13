from django.test import TestCase
from django.urls import reverse
from taggit.models import Tag
from library.models import LibraryItem
from magazine.models import MagazineArticle
from news.models import NewsItem
from wf_pages.factories import WfPageFactory
from news.factories import NewsItemFactory
from magazine.factories import MagazineArticleFactory
from library.factories import LibraryItemFactory
from wf_pages.models import WfPage


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
