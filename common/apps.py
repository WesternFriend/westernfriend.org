import threading

from django.apps import AppConfig
from django.core.signals import request_finished, request_started

# Thread-local storage for the per-request locale cache.
# Each worker thread keeps its own dict that is created at the start of an
# HTTP request and discarded at the end.  Code that runs outside the
# request/response cycle (tests, management commands) sees no cache at all,
# so stale data across database resets is never a problem.
_locale_cache_local = threading.local()


class CommonConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "common"

    def ready(self):
        self._patch_locale_manager()

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
                # Not inside an HTTP request – skip the cache entirely.
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
        request_started.connect(_init_cache)
        request_finished.connect(_clear_cache)
