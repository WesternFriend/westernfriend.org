"""Build dependency integrity and template migration checks."""

import hashlib
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase


class DaisyUIDownloadTests(SimpleTestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.destination = Path(self.directory.name) / "theme/static_src/src"
        self.destination.mkdir(parents=True)
        self.payloads = {"daisyui.mjs": b"plugin", "daisyui-theme.mjs": b"theme"}
        self.hashes = {
            name: hashlib.sha256(data).hexdigest()
            for name, data in self.payloads.items()
        }
        self.override = self.settings(
            BASE_DIR=self.directory.name,
            DAISYUI_SHA256=self.hashes,
        )
        self.override.enable()
        self.addCleanup(self.override.disable)

    def download(self):
        call_command("download_daisyui", stdout=StringIO())

    @patch("common.management.commands.download_daisyui.requests.get")
    def test_downloads_pinned_urls_and_reuses_verified_files(self, get):
        get.side_effect = [Mock(content=data) for data in self.payloads.values()]
        self.download()
        for name, data in self.payloads.items():
            self.assertEqual((self.destination / name).read_bytes(), data)
            get.assert_any_call(
                f"https://github.com/saadeghi/daisyui/releases/download/v{settings.DAISYUI_VERSION}/{name}",
                timeout=60,
            )
        get.reset_mock()
        self.download()
        get.assert_not_called()

    @patch("common.management.commands.download_daisyui.requests.get")
    def test_checksum_failure_preserves_existing_bundles(self, get):
        for name in self.payloads:
            (self.destination / name).write_bytes(b"old")
        get.side_effect = [Mock(content=b"plugin"), Mock(content=b"tampered")]
        with self.assertRaisesMessage(CommandError, "SHA-256 mismatch"):
            self.download()
        for name in self.payloads:
            self.assertEqual((self.destination / name).read_bytes(), b"old")

    @patch("common.management.commands.download_daisyui.requests.get")
    def test_http_failure_stops_build(self, get):
        import requests

        get.return_value.raise_for_status.side_effect = requests.HTTPError("HTTP 404")
        with self.assertRaisesMessage(CommandError, "HTTP 404"):
            self.download()
        self.assertEqual(list(self.destination.iterdir()), [])


class FormLabelTests(SimpleTestCase):
    def test_reader_forms_have_visible_associated_labels(self):
        from copy import deepcopy
        from types import SimpleNamespace

        from bs4 import BeautifulSoup
        from django.template.loader import render_to_string
        from django.test import RequestFactory
        from wagtail.models import Page

        from accounts.forms import CustomUserForm
        from orders.forms import OrderCreateForm

        # Isolate page content from navigation and site settings that need a DB.
        templates = deepcopy(settings.TEMPLATES)
        templates[0]["APP_DIRS"] = False
        templates[0]["OPTIONS"]["loaders"] = [
            (
                "django.template.loaders.locmem.Loader",
                {"base.html": "{% block content %}{% endblock %}"},
            ),
            "django.template.loaders.filesystem.Loader",
            "django.template.loaders.app_directories.Loader",
        ]
        product = Page(id=1, title="Example book")
        product.image = None
        product.get_url = Mock(return_value="/book/")
        contexts = {
            "library/library_index_page.html": {},
            "memorials/memorial_index_page.html": {},
            "magazine/deep_archive_index_page.html": {},
            "search/search.html": {},
            "cart/detail.html": {"cart": [{"product": product, "quantity": 1}]},
            "orders/create.html": {"form": OrderCreateForm()},
            "subscription/register.html": {"form": CustomUserForm()},
            "django_registration/registration_form.html": {"form": CustomUserForm()},
        }
        with self.settings(TEMPLATES=templates):
            for template, extra in contexts.items():
                with self.subTest(template=template):
                    html = render_to_string(
                        template,
                        {
                            "request": RequestFactory().get("/"),
                            "page": SimpleNamespace(title="Example", intro=""),
                            **extra,
                        },
                    )
                    soup = BeautifulSoup(html, "html.parser")
                    controls = soup.select(
                        'input:not([type="hidden"]), select, textarea',
                    )
                    self.assertTrue(controls)
                    for control in controls:
                        label = soup.find("label", attrs={"for": control.get("id")})
                        self.assertIsNotNone(label, str(control))
                        self.assertTrue(label.get_text(strip=True))
                        self.assertNotIn("sr-only", label.get("class", []))
