"""Tests for environment-dependent Django settings."""

import os
import subprocess
import sys

from django.test import SimpleTestCase


class SecretKeySettingsTest(SimpleTestCase):
    """Verify that SECRET_KEY behavior depends on DEBUG and the environment."""

    def _load_settings(self, *, debug, secret_key=None):
        env = os.environ.copy()
        env.pop("DJANGO_SECRET_KEY", None)
        env["DJANGO_DEBUG"] = "true" if debug else "false"
        env["PYTHON_DOTENV_DISABLED"] = "true"
        if secret_key is not None:
            env["DJANGO_SECRET_KEY"] = secret_key

        return subprocess.run(
            [
                sys.executable,
                "-c",
                "import core.settings; print(core.settings.SECRET_KEY)",
            ],
            capture_output=True,
            check=False,
            env=env,
            text=True,
        )

    def test_debug_uses_safe_fallback_when_secret_key_is_missing(self):
        result = self._load_settings(debug=True)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "not-so-secret-key")

    def test_production_fails_clearly_when_secret_key_is_missing(self):
        result = self._load_settings(debug=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "DJANGO_SECRET_KEY must be set when DJANGO_DEBUG is not enabled.",
            result.stderr,
        )

    def test_production_uses_configured_secret_key(self):
        result = self._load_settings(
            debug=False,
            secret_key="configured-test-key",  # noqa: S106 - test fixture only
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "configured-test-key")

    def test_production_fails_clearly_when_secret_key_is_empty(self):
        result = self._load_settings(debug=False, secret_key="")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "DJANGO_SECRET_KEY must be set when DJANGO_DEBUG is not enabled.",
            result.stderr,
        )
