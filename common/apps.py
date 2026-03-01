from django.apps import AppConfig


class CommonConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "common"

    def ready(self):
        self._patch_locale_manager()

    @staticmethod
    def _patch_locale_manager():
        """Cache LocaleManager.get_for_language to avoid a DB hit per call.

        With WAGTAIL_I18N_ENABLED=True, Wagtail 7.3 calls
        Locale.objects.get_for_language() on every page.localized access
        (e.g. once per rich-text page link during template rendering) without
        any caching.  Locale rows are effectively static in production, so a
        simple process-level cache eliminates the N+1.
        """
        from wagtail.models import LocaleManager

        _original = LocaleManager.get_for_language
        _cache: dict = {}

        def _cached(self, language_code):
            if language_code not in _cache:
                _cache[language_code] = _original(self, language_code)
            return _cache[language_code]

        LocaleManager.get_for_language = _cached
