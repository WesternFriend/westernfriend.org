from django.test import TestCase
from django.conf import settings
from wagtail.models import Page, Site

from home.models import HomePage

from .models import ContactFormPage


class ContactFormPageHoneypotTest(TestCase):
    def setUp(self) -> None:
        site_root = Page.objects.get(id=2)

        self.home_page = HomePage(title="Home")
        site_root.add_child(instance=self.home_page)

        Site.objects.all().update(root_page=self.home_page)
        self.contact_form_page = ContactFormPage(
            title="Contact Form Page",
            slug="contact-form-page",
        )
        self.home_page.add_child(instance=self.contact_form_page)

    def test_honeypot_field_is_rendered(self) -> None:
        response = self.client.get(self.contact_form_page.url)
        self.assertContains(
            response,
            settings.HONEYPOT_FIELD_NAME,
        )
