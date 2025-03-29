from django.apps import AppConfig


class MagazineConfig(AppConfig):
    name = "magazine"

    def ready(self):
        """Import signals when app is ready."""
        from . import signals  # noqa

        # Keep signals module imported without using assert
        if not signals:  # This condition will never be true but keeps the import
            pass  # pragma: no cover
