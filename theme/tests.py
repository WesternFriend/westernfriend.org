"""Accessible reader form labels survive CSS framework upgrades."""

from pathlib import Path
from unittest.mock import Mock

from django.conf import settings
from django.test import SimpleTestCase


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
        templates[0]["DIRS"].insert(0, Path(settings.BASE_DIR) / "theme/test_templates")
        templates[0]["OPTIONS"]["loaders"] = [
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
