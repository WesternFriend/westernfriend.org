import threading

from django.apps import AppConfig
from django.core.signals import request_finished, request_started

# Thread-local storage for per-request caches.
# Each worker thread keeps its own state, created at the start of an HTTP
# request and discarded at the end.  Code that runs outside the
# request/response cycle (tests, management commands) sees no cache at all,
# so stale data across database resets is never a problem.
_locale_cache_local = threading.local()
_site_root_paths_local = threading.local()


class CommonConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "common"

    def ready(self):
        from common.signal_handlers import register_signal_handlers

        self._patch_locale_manager()
        self._patch_site_root_paths()
        register_signal_handlers()

    @staticmethod
    def _patch_locale_manager():
        """Cache LocaleManager.get_for_language for the duration of each request.

        Problem
        -------
        With WAGTAIL_I18N_ENABLED=True, Wagtail 7.3's PageLinkHandler calls
        ``page.localized.url`` for every internal link when rendering a
        RichTextBlock.  Each call bottoms out in
        ``LocaleManager.get_for_language()``, which issues an uncached
        ``SELECT … FROM wagtailcore_locale WHERE language_code = %s``.
        A page with many links therefore produces an N+1 of identical queries.

        Fix
        ---
        Wrap ``get_for_language`` so it caches results in a thread-local dict
        that is initialised at ``request_started`` and cleared at
        ``request_finished``.  Outside the request lifecycle the original,
        uncached method is called directly, which keeps tests and management
        commands unaffected by any stale state.
        """
        from django.conf import settings
        from wagtail.models import LocaleManager

        if not getattr(settings, "WAGTAIL_I18N_ENABLED", False):
            return

        if getattr(LocaleManager.get_for_language, "__patched_by_app__", False):
            return

        _original = LocaleManager.get_for_language

        def _cached(self, language_code):
            cache = getattr(_locale_cache_local, "locale_cache", None)
            if cache is None:
                # Not inside an HTTP request - skip the cache entirely.
                return _original(self, language_code)
            if language_code not in cache:
                cache[language_code] = _original(self, language_code)
            return cache[language_code]

        _cached.__patched_by_app__ = True

        def _init_cache(**kwargs):
            _locale_cache_local.locale_cache = {}

        def _clear_cache(**kwargs):
            _locale_cache_local.locale_cache = None

        LocaleManager.get_for_language = _cached
        # weak=False prevents the closures from being garbage-collected after
        # _patch_locale_manager() returns (Django holds only a weakref by default).
        request_started.connect(_init_cache, weak=False)
        request_finished.connect(_clear_cache, weak=False)

    @staticmethod
    def _patch_site_root_paths():
        """Memoize Site.get_site_root_paths for the duration of each request.

        Problem
        -------
        ``Site.get_site_root_paths()`` stores its result in Django's cache.
        With ``DatabaseCache``, that read is a SQL query. Wagtail keeps the
        result on the request when a request is passed (``{% pageurl %}``).
        Calls without one — ``page.url``, ``page.full_url``, and rich text's
        ``PageLinkHandler`` — cache it on the page instance instead, so every
        distinct page does its own cache read.

        Fix
        ---
        Wrap ``get_site_root_paths`` so the first call inside a request runs
        the original method and later calls return that list. The memo is
        created at ``request_started`` and dropped at ``request_finished``.
        ``clear_site_root_paths_cache`` drops it too, so a site save during a
        request is visible to the next call. Outside the request lifecycle
        the original method runs uncached.
        """
        from wagtail.models import Site

        if getattr(Site.get_site_root_paths, "__patched_by_app__", False):
            return

        _original_get = Site.get_site_root_paths
        _original_clear = Site.clear_site_root_paths_cache

        def _cached_get():
            if not getattr(_site_root_paths_local, "active", False):
                return _original_get()
            if not getattr(_site_root_paths_local, "filled", False):
                _site_root_paths_local.paths = _original_get()
                _site_root_paths_local.filled = True
            return _site_root_paths_local.paths

        _cached_get.__patched_by_app__ = True

        def _cached_clear():
            _original_clear()
            if getattr(_site_root_paths_local, "active", False):
                _site_root_paths_local.filled = False
                _site_root_paths_local.paths = None

        def _init_cache(**kwargs):
            _site_root_paths_local.active = True
            _site_root_paths_local.filled = False
            _site_root_paths_local.paths = None

        def _clear_cache(**kwargs):
            _site_root_paths_local.active = False
            _site_root_paths_local.filled = False
            _site_root_paths_local.paths = None

        Site.get_site_root_paths = staticmethod(_cached_get)
        Site.clear_site_root_paths_cache = staticmethod(_cached_clear)
        # weak=False prevents the closures from being garbage-collected after
        # _patch_site_root_paths() returns (Django holds only a weakref by default).
        request_started.connect(_init_cache, weak=False)
        request_finished.connect(_clear_cache, weak=False)
