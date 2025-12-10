from http import HTTPStatus

from django.template import TemplateDoesNotExist
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from wagtail.models import Page
from wagtail.search.backends import get_search_backend

from contact.factories import PersonFactory
from magazine.factories import MagazineArticleFactory, MagazineIssueFactory
from magazine.models import MagazineArticle


class SearchViewTestCase(TestCase):
    def setUp(self) -> None:
        self.client = Client()

        # get the root page
        root_page = Page.objects.first()

        # add test pages as children of the root
        self.page1 = Page(title="Test Page 1")
        root_page.add_child(instance=self.page1)

        self.page2 = Page(title="Test Page 2")
        root_page.add_child(instance=self.page2)

        self.page3 = Page(title="Test Page 3")
        root_page.add_child(instance=self.page3)

        self.page1.save()
        self.page2.save()
        self.page3.save()

        # Update the search index to make the pages searchable
        search_backend = get_search_backend()
        # Add pages one by one to the search index
        for page in Page.objects.all():
            search_backend.add(page)

    def test_search_no_query(self) -> None:
        response = self.client.get(reverse("search"))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(len(response.context["paginated_search_results"].page), 0)

    def test_search_query(self) -> None:
        response = self.client.get(
            reverse("search"),
            {"query": "Test"},
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(len(response.context["paginated_search_results"].page), 3)

    def test_search_pagination_non_existant_page_default_first(self) -> None:
        response = self.client.get(
            reverse("search"),
            {
                "query": "Test",
                "page": 2,
            },
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(len(response.context["paginated_search_results"].page), 3)

    def test_search_pagination_invalid_page(self) -> None:
        response = self.client.get("/search/?query=Test&page=abc")
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.context["paginated_search_results"].page.number, 1)

    def test_search_pagination_out_of_range(self) -> None:
        response = self.client.get("/search/?query=Test&page=100")
        self.assertEqual(response.status_code, HTTPStatus.OK)
        # Page 100 exceeds max_page_limit of 50, so we expect the limit exceeded message
        self.assertTrue(response.context.get("page_limit_exceeded"))
        self.assertIsNone(response.context["paginated_search_results"])


class SearchOptimizationTestCase(TestCase):
    """Test cases to verify that search queries are optimized to avoid N+1 problems."""

    def setUp(self) -> None:
        self.client = Client()

        # Create test data with magazine articles that have authors
        self.magazine_issue = MagazineIssueFactory(title="Test Issue")

        # Create some authors (Person instances)
        self.author1 = PersonFactory(given_name="John", family_name="Doe")
        self.author2 = PersonFactory(given_name="Jane", family_name="Smith")

        # Create magazine articles with authors
        self.article1 = MagazineArticleFactory(
            title="Test Article One",
            parent=self.magazine_issue,
        )
        self.article2 = MagazineArticleFactory(
            title="Test Article Two",
            parent=self.magazine_issue,
        )

        # Add authors to articles
        from magazine.models import MagazineArticleAuthor

        MagazineArticleAuthor.objects.create(article=self.article1, author=self.author1)
        MagazineArticleAuthor.objects.create(article=self.article1, author=self.author2)
        MagazineArticleAuthor.objects.create(article=self.article2, author=self.author1)

        # Update search index
        search_backend = get_search_backend()
        for page in Page.objects.all():
            search_backend.add(page)

    @override_settings(DEBUG=True)
    def test_search_prefetches_related_data(self) -> None:
        """Test that search view prefetches related data to avoid N+1 queries."""

        # Perform the search and capture query count
        # Note: This count includes Django setup queries, search queries, and template rendering
        response = self.client.get(reverse("search"), {"query": "Test Article"})

        # Verify the search worked
        self.assertEqual(response.status_code, HTTPStatus.OK)

        # Now access the data in templates - should not trigger additional queries
        search_results = response.context["paginated_search_results"].page.object_list

        # With perfect prefetching, accessing authors should trigger exactly 0 queries.
        # This verifies that all related data (authors and their linked author pages)
        # has been prefetched by the view.
        with self.assertNumQueries(0):
            for result in search_results:
                if isinstance(result, MagazineArticle):
                    # Access authors - should be prefetched
                    _ = list(result.authors.all())
                    for author_link in result.authors.all():
                        # Access author details - should also be prefetched
                        _ = author_link.author.title if author_link.author else ""

    @override_settings(DEBUG=True)
    def test_search_prefetches_parent_pages(self) -> None:
        """Test that search view prefetches parent pages for magazine articles."""

        # Perform the search
        response = self.client.get(reverse("search"), {"query": "Test Article"})

        # Verify the search worked
        self.assertEqual(response.status_code, HTTPStatus.OK)

        search_results = response.context["paginated_search_results"].page.object_list

        # With parent page prefetching, accessing get_parent().specific should not trigger queries
        with self.assertNumQueries(0):
            for result in search_results:
                if isinstance(result, MagazineArticle):
                    # Access parent page - should be prefetched
                    parent = result.get_parent()
                    # Access specific parent - should also be prefetched
                    _ = parent.specific

    @override_settings(DEBUG=True)
    def test_search_full_request_query_count(self) -> None:
        """Test total queries for complete search request including template rendering.

        This is the most important test - it catches N+1 issues that only appear
        during template rendering (like the parent page issue we had).

        Expected query breakdown for search with 2 magazine articles:

        SEARCH-SPECIFIC QUERIES (12 queries):
        1. Content type lookup for searchable models
        2. Count query for pagination total
        3. Search query (main results with ranking)
        4. Magazine articles with departments (select_related)
        5. Prefetch magazine article authors (MagazineArticleAuthor)
        6. Prefetch author pages (Person pages)
        7. Prefetch article tags
        8. Parent pages lookup (path-based, for magazine issues)
        9. Parent pages .specific() call (convert to MagazineIssue)
        10-11. Additional ancestor queries (for breadcrumbs/navigation in templates)
        12. Magazine index page query (template ancestor navigation)

        BASE TEMPLATE OVERHEAD (7 queries):
        13. Site lookup by hostname (wagtailcore_site)
        14. Default site lookup (wagtailcore_site)
        15. Navigation menu settings (navigation_navigationmenusetting)
        16-17. Navigation settings INSERT (test setup only, not in production)
        18. Site + root page + locale join
        19. Page translation lookup by translation_key

        Total: 19 queries (constant regardless of number of results)

        KEY INSIGHT: Only queries 1-12 scale with search complexity. The base template
        queries (13-19) are the same for ANY page in the site, not search-specific.
        """
        # Count queries for the ENTIRE request/response cycle
        with self.assertNumQueries(19):  # Baseline with all optimizations
            response = self.client.get(reverse("search"), {"query": "Test Article"})

        self.assertEqual(response.status_code, HTTPStatus.OK)
        # Verify we got results
        self.assertGreater(
            len(response.context["paginated_search_results"].page.object_list),
            0,
        )

    @override_settings(DEBUG=True)
    def test_search_query_optimization(self) -> None:
        """Test that search queries are optimized to avoid N+1 database queries."""
        # Perform the search
        response = self.client.get(reverse("search"), {"query": "Test Article"})

        # Verify the search worked
        self.assertEqual(response.status_code, HTTPStatus.OK)
        search_results = response.context["paginated_search_results"].page

        # Find magazine articles in the results (already specific from view)
        magazine_articles = [
            result for result in search_results if isinstance(result, MagazineArticle)
        ]

        # We should have found our test articles
        self.assertGreater(
            len(magazine_articles),
            0,
            "Should have found magazine articles in search results",
        )

        # Now simulate what the template does - access the authors
        # This should NOT trigger additional queries since the view already prefetched everything
        # The results from the view are already specific instances with prefetched data
        with self.assertNumQueries(0):
            for article in magazine_articles:
                # Access authors (this is what the template does)
                authors = list(article.authors.all())
                for author in authors:
                    # Access author details (what template does with author.author.title)
                    # We don't need to store this, just access it to trigger potential queries
                    _ = author.author.title if author.author else "Unknown"

    def test_search_results_include_authors(self) -> None:
        """Test that search results include author information in the response context."""
        response = self.client.get(reverse("search"), {"query": "Test Article"})

        self.assertEqual(response.status_code, HTTPStatus.OK)

        # Verify that the response includes the necessary context
        self.assertIn("paginated_search_results", response.context)

        # Check that magazine articles are found and have accessible authors
        search_results = response.context["paginated_search_results"].page
        magazine_articles = [
            result
            for result in search_results
            if isinstance(result.specific, MagazineArticle)
        ]

        self.assertGreater(len(magazine_articles), 0)

        # Verify that authors are accessible (this would fail if prefetch wasn't working)
        for article in magazine_articles:
            authors = article.specific.authors.all()
            author_count = len(authors)
            # Assert that we have the expected number of authors based on our test data
            # article1 has 2 authors, article2 has 1 author
            self.assertGreater(
                author_count,
                0,
                f"Article '{article.title}' should have at least one author",
            )
            if article.title == "Test Article One":
                self.assertEqual(
                    author_count,
                    2,
                    "Test Article One should have exactly 2 authors",
                )
            elif article.title == "Test Article Two":
                self.assertEqual(
                    author_count,
                    1,
                    "Test Article Two should have exactly 1 author",
                )


class SearchTemplateRenderingTestCase(TestCase):
    """Test cases to verify that search results use custom templates or fallback correctly."""

    def setUp(self) -> None:
        self.client = Client()

        # Create a magazine issue and article (has custom search template)
        self.magazine_issue = MagazineIssueFactory(title="Test Magazine Issue")
        self.author = PersonFactory(given_name="John", family_name="Doe")
        self.article = MagazineArticleFactory(
            title="Test Article with Custom Template",
            parent=self.magazine_issue,
        )

        # Add author to article
        from magazine.models import MagazineArticleAuthor

        MagazineArticleAuthor.objects.create(article=self.article, author=self.author)

        # Create a generic page (no custom search template)
        root_page = Page.objects.first()
        self.generic_page = Page(title="Generic Test Page")
        root_page.add_child(instance=self.generic_page)
        self.generic_page.save()

        # Update search index
        search_backend = get_search_backend()
        for page in Page.objects.all():
            search_backend.add(page)

    def test_magazine_article_uses_custom_template(self) -> None:
        """Test that magazine articles use their custom search template."""
        response = self.client.get(reverse("search"), {"query": "Test Article"})
        self.assertEqual(response.status_code, HTTPStatus.OK)

        # Verify custom template is used
        self.assertTemplateUsed(response, "search/magazine_article.html")

    def test_generic_page_uses_fallback_rendering(self) -> None:
        """Test that generic pages without custom templates use fallback rendering."""
        response = self.client.get(reverse("search"), {"query": "Generic Test"})
        self.assertEqual(response.status_code, HTTPStatus.OK)

        # Should contain fallback card structure
        self.assertContains(response, 'class="card bg-base-100 shadow"')
        self.assertContains(response, 'class="card-body"')
        self.assertContains(response, 'class="card-title text-lg"')

    def test_magazine_article_displays_authors(self) -> None:
        """Test that magazine article search results display author information."""
        response = self.client.get(reverse("search"), {"query": "Test Article"})
        self.assertEqual(response.status_code, HTTPStatus.OK)

        # Should display author name
        self.assertContains(response, "John Doe")

    def test_magazine_article_displays_teaser(self) -> None:
        """Test that magazine article search results can display teaser text."""
        # Update article with teaser
        self.article.teaser = "This is a test teaser for the article"
        self.article.save()

        # Update search index
        search_backend = get_search_backend()
        search_backend.add(self.article)

        response = self.client.get(reverse("search"), {"query": "Test Article"})
        self.assertEqual(response.status_code, HTTPStatus.OK)

        # Should display teaser text
        self.assertContains(response, "This is a test teaser for the article")

    def test_search_results_use_semantic_html(self) -> None:
        """Test that search results use semantic HTML elements."""
        response = self.client.get(reverse("search"), {"query": "Test"})
        self.assertEqual(response.status_code, HTTPStatus.OK)

        # Should use article tags for search results
        self.assertContains(response, "<article")

    def test_search_results_have_accessible_links(self) -> None:
        """Test that search result links are accessible."""
        response = self.client.get(reverse("search"), {"query": "Test Article"})
        self.assertEqual(response.status_code, HTTPStatus.OK)

        # Links should have descriptive text (article title)
        self.assertContains(response, "href=")
        self.assertContains(response, "Test Article with Custom Template")

    def test_search_pagination_limit_message(self) -> None:
        """Test that pagination limit exceeded message is displayed when appropriate."""
        response = self.client.get(reverse("search"), {"query": "Test", "page": "100"})
        self.assertEqual(response.status_code, HTTPStatus.OK)

        # Should show limit exceeded message
        self.assertContains(response, "Too many results to display")
        self.assertContains(response, "Search results are limited to 50 pages")
        self.assertContains(response, "Please refine your search")

    def test_search_no_results_empty_list(self) -> None:
        """Test that no results returns an empty list."""
        response = self.client.get(
            reverse("search"),
            {"query": "NonexistentSearchTerm12345"},
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

        # Should have paginated_search_results in context
        self.assertIn("paginated_search_results", response.context)

        # The page should be empty when no results found
        if response.context["paginated_search_results"]:
            self.assertEqual(len(response.context["paginated_search_results"].page), 0)

    def test_search_results_aria_labels(self) -> None:
        """Test that search results have proper ARIA labels for accessibility."""
        response = self.client.get(reverse("search"), {"query": "Test Article"})
        self.assertEqual(response.status_code, HTTPStatus.OK)

        # Should have ARIA labels on sections
        self.assertContains(response, 'aria-label="Search results"')

    def test_fallback_renders_page_title_as_link(self) -> None:
        """Test that fallback rendering shows page title as a clickable link."""
        response = self.client.get(reverse("search"), {"query": "Generic Test"})
        self.assertEqual(response.status_code, HTTPStatus.OK)

        # Should contain the page title
        self.assertContains(response, "Generic Test Page")

        # Title should be wrapped in a link
        self.assertContains(response, "<a href=")


class SearchTemplateConsistencyTestCase(TestCase):
    """Test cases to verify consistency across different search result templates."""

    def setUp(self) -> None:
        from django.template.loader import get_template

        self.template_loader = get_template

    def test_custom_search_templates_exist(self) -> None:
        """Test that expected custom search templates exist."""
        # All custom search templates should exist
        expected_templates = [
            "search/magazine_article.html",
            "search/event.html",
            "search/meeting.html",
            "search/organization.html",
            "search/library_item.html",
            "search/online_worship.html",
            "search/magazine_issue.html",
            "search/community_directory.html",
        ]

        for template_name in expected_templates:
            with self.subTest(template=template_name):
                try:
                    template = self.template_loader(template_name)
                    self.assertIsNotNone(template)
                except TemplateDoesNotExist as e:
                    self.fail(f"Template {template_name} should exist: {e}")


class CustomSearchTemplateRenderingTestCase(TestCase):
    """Test that each content type with a custom search template renders correctly.

    Note: Django's TestCase provides transaction isolation, so each test runs
    in its own transaction and database changes are rolled back after each test.
    This ensures search index isolation between tests.
    """

    def setUp(self) -> None:
        self.client = Client()
        self.search_backend = get_search_backend()

    def _index_and_search(self, page: Page, query: str):
        """Helper to index a page and search for it.

        The database search backend works synchronously, so the page is
        immediately searchable after adding it to the index.
        """
        self.search_backend.add(page)
        response = self.client.get(reverse("search"), {"query": query})
        self.assertEqual(response.status_code, HTTPStatus.OK)
        return response

    def test_magazine_article_custom_template_renders(self) -> None:
        """Test that magazine article search results use custom template with author info."""
        from magazine.models import MagazineArticleAuthor

        # Create test data
        issue = MagazineIssueFactory(title="Test Issue SearchTemplate")
        author = PersonFactory(given_name="Jane", family_name="Author")
        article = MagazineArticleFactory(
            title="Article SearchTemplate Test",
            teaser="This is a test teaser",
            parent=issue,
        )
        MagazineArticleAuthor.objects.create(article=article, author=author)

        response = self._index_and_search(article, "SearchTemplate")

        # Should contain author information (unique to magazine article template)
        self.assertContains(response, "Authors:")
        self.assertContains(response, "Jane Author")

        # Should contain teaser
        self.assertContains(response, "This is a test teaser")

        # Should contain link to parent issue
        self.assertContains(response, "Issue:")
        self.assertContains(response, "Test Issue SearchTemplate")

        # Should have unique debug class
        self.assertContains(response, 'class="search-result-magazine-article"')

    def test_event_custom_template_renders(self) -> None:
        """Test that event search results use custom template."""
        from events.factories import EventFactory

        event = EventFactory(
            title="Event SearchTemplate Test",
            teaser="Event teaser text",
        )

        response = self._index_and_search(event, "SearchTemplate")

        # Should render the event title
        self.assertContains(response, "Event SearchTemplate Test")

        # Should use the custom template card structure
        self.assertContains(response, 'class="card bg-base-100 shadow mb-4"')

        # Should have unique debug class
        self.assertContains(response, 'class="search-result-event"')

        # Note: The event template checks for entity.specific.date but the Event model
        # uses start_date, so the calendar icon won't render. This is a template bug.

    def test_meeting_custom_template_renders(self) -> None:
        """Test that meeting search results use custom template."""
        from contact.factories import MeetingFactory

        meeting = MeetingFactory(
            title="Meeting SearchTemplate Test",
            description="<p>Meeting description here</p>",
        )

        response = self._index_and_search(meeting, "SearchTemplate")

        # Meeting template renders description
        self.assertContains(response, "Meeting description here")

        # Should have card structure
        self.assertContains(response, 'class="card bg-base-100 shadow mb-4"')

        # Should have unique debug class
        self.assertContains(response, 'class="search-result-meeting"')

    def test_organization_custom_template_renders(self) -> None:
        """Test that organization search results use custom template."""
        from contact.factories import OrganizationFactory

        org = OrganizationFactory(
            title="Organization SearchTemplate Test",
            description="<p>Organization description here</p>",
        )

        response = self._index_and_search(org, "SearchTemplate")

        # Organization template renders description
        self.assertContains(response, "Organization description here")

        # Should have unique debug class
        self.assertContains(response, 'class="search-result-organization"')

    def test_library_item_custom_template_renders(self) -> None:
        """Test that library item search results use custom template."""
        from library.factories import LibraryItemFactory

        library_item = LibraryItemFactory(
            title="Library SearchTemplate Test",
        )

        response = self._index_and_search(library_item, "SearchTemplate")

        # Should render the library item title
        self.assertContains(response, "Library SearchTemplate Test")

        # Should have unique debug class
        self.assertContains(response, 'class="search-result-library-item"')

    def test_online_worship_custom_template_renders(self) -> None:
        """Test that online worship search results use custom template."""
        from community.factories import OnlineWorshipFactory

        online_worship = OnlineWorshipFactory(
            title="OnlineWorship SearchTemplate Test",
        )

        response = self._index_and_search(online_worship, "SearchTemplate")

        # Should render the title in the custom template structure
        self.assertContains(response, "OnlineWorship SearchTemplate Test")

        # Should have card structure
        self.assertContains(response, 'class="card bg-base-100 shadow mb-4"')

        # Should have unique debug class
        self.assertContains(response, 'class="search-result-online-worship"')

    def test_magazine_issue_custom_template_renders(self) -> None:
        """Test that magazine issue search results use custom template."""
        from datetime import date

        issue = MagazineIssueFactory(
            title="MagazineIssue SearchTemplate Test",
            publication_date=date(2025, 12, 1),
        )

        response = self._index_and_search(issue, "SearchTemplate")

        # Should render the magazine issue title
        self.assertContains(response, "MagazineIssue SearchTemplate Test")

        # Should have unique debug class
        self.assertContains(response, 'class="search-result-magazine-issue"')

        # Should render publication date
        self.assertContains(response, "December 2025")

    def test_fallback_template_for_pages_without_custom_template(self) -> None:
        """Test that pages without custom search templates use fallback rendering."""
        root_page = Page.objects.first()
        generic_page = Page(title="Generic SearchTemplate Test")
        root_page.add_child(instance=generic_page)
        generic_page.save()

        response = self._index_and_search(generic_page, "SearchTemplate")

        # Should use fallback card structure
        self.assertContains(response, 'class="card bg-base-100 shadow"')
        self.assertContains(response, 'class="card-body"')
        self.assertContains(response, "Generic SearchTemplate Test")

        # Should have unique debug class for fallback
        self.assertContains(response, 'class="search-result-fallback"')

        # Should NOT contain custom template elements
        self.assertNotContains(response, "Authors:")
        self.assertNotContains(response, "bi-calendar-event")
        self.assertNotContains(response, "Issue:")
