from django.db import models
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.contrib.forms.panels import FormSubmissionsPanel
from wagtail.contrib.forms.models import AbstractForm, AbstractFormField
from wagtail.fields import RichTextField


class FormField(AbstractFormField):
    page = ParentalKey(
        "ContactFormPage", on_delete=models.CASCADE, related_name="form_fields"
    )


class ContactFormPage(AbstractForm):
    intro = RichTextField(blank=True)
    thank_you_text = RichTextField(blank=True)

    max_count = 1

    content_panels = AbstractForm.content_panels + [
        FormSubmissionsPanel(),
        FieldPanel("intro", classname="full"),
        InlinePanel("form_fields", label="Form fields"),
        FieldPanel("thank_you_text", classname="full"),
    ]

    parent_page_types = ["home.HomePage"]
    subpage_types = []
