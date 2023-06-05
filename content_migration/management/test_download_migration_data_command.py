from django.test import SimpleTestCase

from content_migration.management.commands.download_migration_data import (
    Command,
)


class CommandSimpleTestCase(SimpleTestCase):
    def test_command_is_callable(self) -> None:
        command = Command()
        self.assertTrue(callable(command.handle))
