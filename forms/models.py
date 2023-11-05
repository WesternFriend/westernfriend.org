from django.db import models
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.contrib.forms.models import AbstractForm, AbstractFormField
from wagtail.contrib.forms.panels import FormSubmissionsPanel
from wagtail.fields import RichTextField
from wagtailcaptcha.models import WagtailCaptchaEmailForm


class FormField(AbstractFormField):
    page = ParentalKey(
        "ContactFormPage",
        on_delete=models.CASCADE,
        related_name="form_fields",
    )


class ContactFormPage(WagtailCaptchaEmailForm):
    intro = RichTextField(blank=True)
    thank_you_text = RichTextField(blank=True)

    max_count = 1

    content_panels = AbstractForm.content_panels + [
        FormSubmissionsPanel(),
        FieldPanel("intro", classname="full"),
        FieldPanel("thank_you_text", classname="full"),
        InlinePanel("form_fields", label="Form fields"),
        MultiFieldPanel(
            [
                FieldPanel(
                    "from_address",
                    help_text="Sender of the submission notification email.",
                ),
                FieldPanel("to_address"),
                FieldPanel(
                    "subject",
                    help_text="Subject of the submission notification email.",
                ),
            ],
            heading="Email Settings",
        ),
    ]

    parent_page_types = ["home.HomePage"]
    subpage_types: list[str] = []
