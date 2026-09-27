from unittest.mock import MagicMock, patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.signals import request_finished, request_started
from django.forms import CharField, TextInput
from django.forms.forms import Form
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.test import RequestFactory, TestCase, override_settings
from wagtail.models import Locale, Page, PageViewRestriction, Site

from common.apps import CommonConfig, _locale_cache_local
from common.middleware import PublicCacheControlMiddleware
from common.templatetags.common_form_tags import add_class
from common.templatetags.common_tags import (
    absolute_static,
    canonical_url,
    exclude_from_breadcrumbs,
    model_name,
    site_root_url,
    specific_pages,
    visible_breadcrumb_ancestors,
)
from home.models import HomePage
from store.factories import ProductFactory


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
            "homepage",
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


class AbsoluteStaticTagTest(TestCase):
    """Tests for the absolute_static template tag."""

    def test_relative_static_url_becomes_absolute(self):
        request = RequestFactory().get("/")

        url = absolute_static({"request": request}, "img/WF-header.png")

        self.assertEqual(url, "http://testserver/static/img/WF-header.png")

    @override_settings(STATIC_URL="https://cdn.example.com/static/")
    def test_absolute_static_url_is_kept(self):
        request = RequestFactory().get("/")

        url = absolute_static({"request": request}, "img/WF-header.png")

        self.assertEqual(url, "https://cdn.example.com/static/img/WF-header.png")

    @override_settings(
        STATIC_URL="https://sfo3.digitaloceanspaces.com/westernfriend-website/static/",
    )
    def test_footer_json_ld_logo_uses_static_url(self):
        html = render_to_string("footer.html", request=RequestFactory().get("/"))

        self.assertIn(
            '"logo": "https://sfo3.digitaloceanspaces.com/westernfriend-website/'
            'static/img/WF-header.png"',
            html,
        )

    def test_without_request_returns_static_url(self):
        self.assertEqual(
            absolute_static({}, "img/WF-header.png"),
            "/static/img/WF-header.png",
        )


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

    def _make_page(self, model_name, *, is_root=False):
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
        """Calling _patch_locale_manager() a second time does not stack wrappers.

        The test explicitly enables i18n and applies the patch once so that the
        assertion is always testing the 'already patched' path, not a trivial
        no-op caused by WAGTAIL_I18N_ENABLED being False at startup.
        """
        from wagtail.models import LocaleManager

        with self.settings(WAGTAIL_I18N_ENABLED=True):
            CommonConfig._patch_locale_manager()  # ensure patch is applied
            before = LocaleManager.get_for_language
            CommonConfig._patch_locale_manager()  # second call must be a no-op
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


@override_settings(PUBLIC_CACHE_EDGE_TTL=900, PUBLIC_CACHE_BROWSER_TTL=60)
class PublicCacheControlMiddlewareTests(TestCase):
    """Only anonymous responses with no visitor state may be cached publicly."""

    def setUp(self):
        self.factory = RequestFactory()
        self.response = HttpResponse("page")
        self.middleware = PublicCacheControlMiddleware(lambda _request: self.response)

    def _request(self, method="get", path="/magazine/", user=None, **kwargs):
        request = getattr(self.factory, method)(path, **kwargs)
        request.user = user or AnonymousUser()
        return request

    def _cache_control(self, request):
        return self.middleware(request)["Cache-Control"]

    def test_anonymous_page_is_public(self):
        self.assertEqual(
            self._cache_control(self._request()),
            'public, max-age=60, s-maxage=900, private="Set-Cookie"',
        )

    def test_head_request_is_public(self):
        self.assertIn("public", self._cache_control(self._request(method="head")))

    @override_settings(PUBLIC_CACHE_EDGE_TTL=0)
    def test_disabled_when_edge_ttl_is_zero(self):
        self.assertEqual(self._cache_control(self._request()), "private")

    def test_authenticated_user_is_private(self):
        user = MagicMock(is_authenticated=True)
        self.assertEqual(self._cache_control(self._request(user=user)), "private")

    def test_request_with_session_cookie_is_private(self):
        request = self._request()
        request.COOKIES[settings.SESSION_COOKIE_NAME] = "abc"
        self.assertEqual(self._cache_control(request), "private")

    def test_response_setting_a_cookie_is_private(self):
        self.response.set_cookie("csrftoken", "abc")
        self.assertEqual(self._cache_control(self._request()), "private")

    def test_post_is_private(self):
        self.assertEqual(self._cache_control(self._request(method="post")), "private")

    def test_non_200_status_is_private(self):
        for status in (301, 302, 404, 500):
            with self.subTest(status=status):
                self.response.status_code = status
                self.assertEqual(self._cache_control(self._request()), "private")

    def test_private_paths_are_private(self):
        for path in ("/admin/", "/accounts/login/", "/cart/", "/paypal/x/"):
            with self.subTest(path=path):
                request = self._request(path=path)
                self.assertEqual(self._cache_control(request), "private")

    def test_existing_cache_control_is_kept(self):
        self.response["Cache-Control"] = "no-cache"
        self.assertEqual(self._cache_control(self._request()), "no-cache")


@override_settings(PUBLIC_CACHE_EDGE_TTL=900)
class PublicCacheControlIntegrationTests(TestCase):
    """The middleware sees the cookies the rest of the stack adds."""

    def setUp(self):
        Locale.objects.get_or_create(language_code="en")
        Site.objects.all().delete()
        root = Page.get_first_root_node() or Page.add_root(title="Root", slug="root")
        home = root.add_child(instance=HomePage(title="Home", slug="cache-home"))
        Site.objects.create(hostname="testserver", root_page=home, is_default_site=True)
        Site.clear_site_root_paths_cache()
        self.addCleanup(Site.clear_site_root_paths_cache)

    def test_anonymous_home_page_is_public(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.cookies)
        self.assertIn("public", response["Cache-Control"])

    def test_logged_in_home_page_is_private(self):
        user = get_user_model().objects.create_user(
            email="reader@example.com",
            password="unused-test-password",
        )
        self.client.force_login(user)

        response = self.client.get("/")

        self.assertEqual(response["Cache-Control"], "private")

    def test_page_with_csrf_token_is_private(self):
        product = ProductFactory()

        response = self.client.get(product.url)

        self.assertEqual(response.status_code, 200)
        self.assertIn("csrftoken", response.cookies)
        self.assertEqual(response["Cache-Control"], "private")

    def test_page_with_csrf_token_is_private_for_returning_visitor(self):
        product = ProductFactory()
        self.client.get(product.url)  # issues the visitor a CSRF cookie
        self.assertIn(settings.CSRF_COOKIE_NAME, self.client.cookies)

        response = self.client.get(product.url)

        self.assertEqual(response["Cache-Control"], "private")


class BreadcrumbsAbsoluteUrlTest(TestCase):
    """Breadcrumb JSON-LD URLs come from the Wagtail site, not request.site."""

    def setUp(self):
        from wagtail.models import Page, Site

        Site.objects.all().delete()
        root = Page.get_first_root_node()
        self.home = root.add_child(instance=Page(title="Home", slug="bc-abs-home"))
        section = self.home.add_child(instance=Page(title="Section", slug="section"))
        self.page = section.add_child(instance=Page(title="Article", slug="article"))
        Site.objects.create(
            hostname="testserver",
            root_page=self.home,
            is_default_site=True,
        )
        Site.clear_site_root_paths_cache()
        self.addCleanup(Site.clear_site_root_paths_cache)

    def test_json_ld_items_are_absolute(self):
        request = RequestFactory().get("/section/article/")

        output = render_to_string(
            "breadcrumbs.html",
            {"page": self.page, "request": request},
            request=request,
        )

        self.assertIn('"item": "http://testserver/"', output)
        self.assertIn('"item": "http://testserver/section/"', output)
        self.assertIn('"item": "http://testserver/section/article/"', output)
        self.assertNotIn("http:///", output)


@override_settings(ALLOWED_HOSTS=["*"])
class CanonicalUrlTagTest(TestCase):
    """canonical_url and site_root_url use the Wagtail site's hostname."""

    def setUp(self):
        from wagtail.models import Page, Site

        Site.objects.all().delete()
        home = Page.get_first_root_node().add_child(
            instance=Page(title="Home", slug="canonical-home"),
        )
        Site.objects.create(
            hostname="example.org",
            port=443,
            root_page=home,
            is_default_site=True,
        )
        Site.clear_site_root_paths_cache()
        self.addCleanup(Site.clear_site_root_paths_cache)

    def test_non_page_view_uses_site_hostname(self):
        request = RequestFactory().get("/search/", HTTP_HOST="www.example.org")

        self.assertEqual(
            canonical_url({"request": request}),
            "https://example.org/search/",
        )

    def test_site_root_url_uses_site_hostname(self):
        request = RequestFactory().get("/", HTTP_HOST="www.example.org")

        self.assertEqual(site_root_url({"request": request}), "https://example.org/")

    def test_falls_back_to_request_host_without_a_site(self):
        from wagtail.models import Site

        Site.objects.all().delete()
        Site.clear_site_root_paths_cache()
        request = RequestFactory().get("/tags/")

        self.assertEqual(canonical_url({"request": request}), "http://testserver/tags/")
        self.assertEqual(site_root_url({"request": request}), "http://testserver/")

    def test_without_request_returns_empty_string(self):
        self.assertEqual(canonical_url({}), "")
        self.assertEqual(site_root_url({}), "")


class PurgeRestrictedPagesTest(TestCase):
    """Changing who may view a page purges its subtree from Cloudflare."""

    def setUp(self):
        Locale.objects.get_or_create(language_code="en")
        root = Page.get_first_root_node() or Page.add_root(title="Root", slug="root")
        self.parent = root.add_child(instance=HomePage(title="Parent", slug="p"))
        self.child = self.parent.add_child(instance=HomePage(title="Child", slug="c"))

    def _purged_pages(self, change):
        with (
            patch("common.signal_handlers.PurgeBatch") as purge_batch,
            self.captureOnCommitCallbacks(execute=True),
        ):
            change()
        batch = purge_batch.return_value
        batch.purge.assert_called_once_with()
        return set(batch.add_pages.call_args.args[0])

    def test_adding_a_restriction_purges_page_and_descendants(self):
        pages = self._purged_pages(
            lambda: PageViewRestriction.objects.create(
                page=self.parent,
                restriction_type=PageViewRestriction.LOGIN,
            ),
        )

        self.assertEqual(pages, {self.parent.specific, self.child.specific})

    def test_removing_a_restriction_purges_the_page(self):
        restriction = PageViewRestriction.objects.create(
            page=self.child,
            restriction_type=PageViewRestriction.LOGIN,
        )

        pages = self._purged_pages(restriction.delete)

        self.assertEqual(pages, {self.child.specific})


class FakeMessage:
    def __init__(self, tags: str, text: str) -> None:
        self.tags = tags
        self.text = text

    def __str__(self) -> str:
        return self.text


class FlashMessageRolesTest(TestCase):
    """Errors are announced assertively; other messages politely."""

    def test_message_roles_match_severity(self) -> None:
        request = RequestFactory().get("/")
        request.user = AnonymousUser()
        messages = [
            FakeMessage("error", "Payment failed"),
            FakeMessage("success", "Order placed"),
        ]

        html = render_to_string("base.html", {"messages": messages}, request=request)

        self.assertRegex(
            html,
            r'role="alert"[^>]*>\s*<i[^>]*>\s*</i>\s*<span>Payment failed',
        )
        self.assertRegex(
            html,
            r'role="status"[^>]*>\s*<i[^>]*>\s*</i>\s*<span>Order placed',
        )
