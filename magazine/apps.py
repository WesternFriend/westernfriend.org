from django.apps import AppConfig


class MagazineConfig(AppConfig):
    name = "magazine"

    def ready(self):
        """Import signals when app is ready."""
        from . import signals  # noqa

        # Prevent linter from complaining about unused import
        # since it is necessary for signal registration
        # and not used directly in the code.
        if not signals:  # This condition will never be true but keeps the import
            pass  # pragma: no cover
