from unittest.mock import MagicMock

from django.conf import settings
from django.core.signals import request_finished, request_started
from django.forms import CharField, TextInput
from django.forms.forms import Form
from django.template.loader import render_to_string
from django.test import RequestFactory, TestCase

from common.apps import CommonConfig, _locale_cache_local
from common.templatetags.common_form_tags import add_class
from common.templatetags.common_tags import (
    exclude_from_breadcrumbs,
    model_name,
    specific_pages,
    visible_breadcrumb_ancestors,
)


class MockModel:
    """Mock model class for testing template tags."""

    class _meta:
        model_name = "mockmodel"


class CommonFormTagsTests(TestCase):
    """Tests for common form tags template filters."""

    def setUp(self):
        """Set up test data."""

        # Create a simple form with a single field
        class TestForm(Form):
            test_field = CharField(
                widget=TextInput(attrs={"class": "existing-class"}),
            )
            no_class_field = CharField(widget=TextInput())

        self.form = TestForm()
        self.field_with_class = self.form["test_field"]
        self.field_without_class = self.form["no_class_field"]

    def test_add_class(self):
        """Test the add_class filter adds CSS classes correctly."""
        # Test adding a class to a field with existing class
        result = add_class(self.field_with_class, "new-class")
        self.assertIn('class="new-class existing-class"', result)

        # Test adding multiple classes
        result = add_class(self.field_with_class, "class1 class2")
        self.assertIn('class="class1 class2 existing-class"', result)

        # Test adding a class to a field without existing class
        result = add_class(self.field_without_class, "new-class")
        self.assertIn('class="new-class "', result)

        # Test with empty class string
        result = add_class(self.field_with_class, "")
        self.assertIn('class=" existing-class"', result)


class CommonTagsTests(TestCase):
    """Tests for common tags template filters."""

    def test_model_name(self):
        """Test the model_name filter returns the correct model name."""
        # Test with a valid model object
        mock_model = MockModel()
        self.assertEqual(model_name(mock_model), "mockmodel")

        # Test with None
        self.assertEqual(model_name(None), "")

        # Test with an object that has no _meta attribute
        class NoMetaObject:
            pass

        self.assertEqual(model_name(NoMetaObject()), "")

    def test_exclude_from_breadcrumbs(self):
        """Test the exclude_from_breadcrumbs filter."""

        # Test with a page that should be excluded
        class PersonIndexPage:
            class _meta:
                model_name = (
                    "personindexpage"  # This is a string attribute, not a function
                )

        mock_page = PersonIndexPage()
        self.assertTrue(exclude_from_breadcrumbs(mock_page))

        # Test with a page that should not be excluded
        class RegularPage:
            class _meta:
                model_name = "regularpage"

        self.assertFalse(exclude_from_breadcrumbs(RegularPage()))

        # Test with None
        self.assertFalse(exclude_from_breadcrumbs(None))

        # Test with an object that has no _meta attribute
        class NoMetaObject:
            pass

        self.assertFalse(exclude_from_breadcrumbs(NoMetaObject()))

        # Test with all excluded model types
        excluded_models = [
            "personindexpage",
            "meetingindexpage",
            "organizationindexpage",
            "facetindexpage",
            "audienceindexpage",
            "genreindexpage",
            "mediumindexpage",
            "timeperiodindexpage",
            "topicindexpage",
            "productindexpage",
        ]

        for excluded_model in excluded_models:

            class ExcludedPage:
                class _meta:
                    model_name = excluded_model  # Using the string from the list

            self.assertTrue(exclude_from_breadcrumbs(ExcludedPage()))


class SpecificPagesFilterTest(TestCase):
    """Tests for the specific_pages template filter."""

    def test_calls_specific_on_queryset(self):
        """specific_pages delegates to queryset.specific()."""
        mock_qs = MagicMock()
        mock_qs.specific.return_value = sentinel = object()
        self.assertIs(specific_pages(mock_qs), sentinel)
        mock_qs.specific.assert_called_once_with()

    def test_returns_result_of_specific(self):
        """Return value is whatever .specific() produces."""
        mock_qs = MagicMock()
        mock_qs.specific.return_value = ["page_a", "page_b"]
        self.assertEqual(specific_pages(mock_qs), ["page_a", "page_b"])

    def test_returns_falsy_input_unchanged(self):
        """None and other falsy values are returned without calling .specific()."""
        self.assertIsNone(specific_pages(None))
        self.assertEqual(specific_pages([]), [])


class VisibleBreadcrumbAncestorsTest(TestCase):
    """Tests for the visible_breadcrumb_ancestors template filter."""

    def _make_page(self, model_name, is_root=False):
        page = MagicMock()
        page.is_root.return_value = is_root
        page._meta.model_name = model_name
        return page

    def test_falsy_input_returns_empty_list(self):
        self.assertEqual(visible_breadcrumb_ancestors(None), [])
        self.assertEqual(visible_breadcrumb_ancestors([]), [])

    def test_excludes_root_pages(self):
        root = self._make_page("page", is_root=True)
        normal = self._make_page("page", is_root=False)
        self.assertEqual(visible_breadcrumb_ancestors([root, normal]), [normal])

    def test_excludes_breadcrumb_excluded_models(self):
        excluded = self._make_page("personindexpage")
        normal = self._make_page("magazineissue")
        result = visible_breadcrumb_ancestors([excluded, normal])
        self.assertEqual(result, [normal])

    def test_preserves_order_of_visible_ancestors(self):
        a = self._make_page("magazineissue")
        b = self._make_page("magazinearticle")
        self.assertEqual(visible_breadcrumb_ancestors([a, b]), [a, b])


class LocaleCacheTest(TestCase):
    """Tests for the per-request LocaleManager.get_for_language cache.

    The cache is thread-local and is activated only for the lifetime of an
    HTTP request (between request_started and request_finished signals).
    Outside that window - which includes ordinary unit-test code - the
    original uncached method is used, preventing stale data across test
    database resets.
    """

    def setUp(self):
        # Ensure every test begins outside any request.
        _locale_cache_local.locale_cache = None

    def tearDown(self):
        # Leave the thread in a clean state for subsequent tests.
        _locale_cache_local.locale_cache = None

    def test_patch_is_idempotent(self):
        """Calling _patch_locale_manager() a second time does not stack wrappers."""
        from wagtail.models import LocaleManager

        before = LocaleManager.get_for_language
        CommonConfig._patch_locale_manager()
        self.assertIs(LocaleManager.get_for_language, before)

    def test_patch_skipped_when_i18n_disabled(self):
        """No wrapping occurs when WAGTAIL_I18N_ENABLED is falsy."""
        from wagtail.models import LocaleManager

        with self.settings(WAGTAIL_I18N_ENABLED=False):
            original = LocaleManager.get_for_language
            CommonConfig._patch_locale_manager()
            self.assertIs(LocaleManager.get_for_language, original)

    def test_cache_is_none_outside_request(self):
        """No cache dict exists before a request starts."""
        self.assertIsNone(getattr(_locale_cache_local, "locale_cache", None))

    def test_request_started_initialises_cache(self):
        """request_started creates an empty cache dict."""
        request_started.send(sender=None, environ={})
        self.assertIsInstance(_locale_cache_local.locale_cache, dict)
        self.assertEqual(_locale_cache_local.locale_cache, {})

    def test_request_finished_clears_cache(self):
        """request_finished sets the cache back to None."""
        request_started.send(sender=None, environ={})
        request_finished.send(sender=None)
        self.assertIsNone(_locale_cache_local.locale_cache)

    def test_locale_cached_within_request(self):
        """Two calls within the same request return the identical object.

        The cache is activated directly (rather than via request_started) to
        avoid Django's close_old_connections handler tearing down the test DB
        connection as a side-effect of sending that signal.
        """
        from wagtail.models import Locale

        _locale_cache_local.locale_cache = {}
        first = Locale.objects.get_for_language(settings.LANGUAGE_CODE)
        second = Locale.objects.get_for_language(settings.LANGUAGE_CODE)
        self.assertIs(first, second)

    def test_no_cross_request_cache_leakage(self):
        """Each new request starts with a fresh, empty cache."""
        request_started.send(sender=None, environ={})
        request_finished.send(sender=None)

        request_started.send(sender=None, environ={})
        try:
            self.assertEqual(
                _locale_cache_local.locale_cache,
                {},
                "Cache should be empty at the start of a new request.",
            )
        finally:
            request_finished.send(sender=None)


class BreadcrumbsTemplateTest(TestCase):
    """Rendering tests for breadcrumbs.html.

    Uses a real Wagtail page tree so that get_ancestors(), specific_pages(),
    and pageurl all exercise their normal code paths, giving the template
    measurable coverage.
    """

    @classmethod
    def setUpTestData(cls):
        from wagtail.models import Page, Site

        try:
            root = Page.objects.get(depth=1)
        except Page.DoesNotExist:
            root = Page.add_root(title="Root", slug="root")

        cls.home = root.add_child(
            instance=Page(title="BC Home", slug="bc-test-home"),
        )
        cls.child = cls.home.add_child(
            instance=Page(title="BC Child", slug="bc-test-child"),
        )

        # Ensure a default site exists so pageurl can resolve URLs.
        cls.site = Site.objects.filter(is_default_site=True).first()
        if cls.site is None:
            cls.site = Site.objects.create(
                hostname="localhost",
                port=80,
                root_page=root,
                is_default_site=True,
                site_name="Test",
            )

    def _render(self, page):
        request = RequestFactory().get("/")
        request.site = self.site
        return render_to_string(
            "breadcrumbs.html",
            {"page": page, "request": request},
            request=request,
        )

    def test_no_output_when_page_is_none(self):
        """Template produces no output when page is None."""
        self.assertEqual(self._render(None).strip(), "")

    def test_no_output_for_shallow_page(self):
        """No breadcrumbs for a page with only one ancestor (the root)."""
        self.assertEqual(self._render(self.home).strip(), "")

    def test_nav_rendered_for_deep_page(self):
        """Breadcrumb nav appears when the page has more than one ancestor."""
        output = self._render(self.child)
        self.assertIn('aria-label="Breadcrumb"', output)
        self.assertIn("BC Home", output)

    def test_current_page_marked_with_aria_current(self):
        """Current page item carries aria-current=page."""
        output = self._render(self.child)
        self.assertIn('aria-current="page"', output)
        self.assertIn("BC Child", output)

    def test_json_ld_included(self):
        """JSON-LD script block is present for deep pages."""
        output = self._render(self.child)
        self.assertIn("application/ld+json", output)
        self.assertIn("BreadcrumbList", output)

    def test_json_ld_positions_are_sequential(self):
        """JSON-LD positions: Home=1, visible ancestor=2, current page=3."""
        output = self._render(self.child)
        self.assertIn('"position": 1', output)
        self.assertIn('"position": 2', output)
        self.assertIn('"position": 3', output)
