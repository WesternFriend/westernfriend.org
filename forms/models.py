from django.db import models
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.contrib.forms.models import (
    AbstractForm,
    AbstractEmailForm,
    AbstractFormField,
)
from wagtail.contrib.forms.panels import FormSubmissionsPanel
from wagtail.fields import RichTextField
from wagtail.contrib.forms.forms import FormBuilder
from django_recaptcha.fields import ReCaptchaField


def remove_captcha_field(form):
    form.fields.pop(WfCaptchaFormBuilder.CAPTCHA_FIELD_NAME, None)
    form.cleaned_data.pop(WfCaptchaFormBuilder.CAPTCHA_FIELD_NAME, None)


class WfCaptchaFormBuilder(FormBuilder):
    CAPTCHA_FIELD_NAME = "wfcaptcha"

    @property
    def formfields(self):
        fields = super().formfields
        fields[self.CAPTCHA_FIELD_NAME] = ReCaptchaField(label="")

        return fields


class WfCaptchaEmailForm(AbstractEmailForm):
    """Pages implementing a captcha form with email notification should inhert
    from this."""

    form_builder = WfCaptchaFormBuilder

    def process_form_submission(self, form):
        remove_captcha_field(form)
        return super().process_form_submission(form)

    class Meta:
        abstract = True


# Form field for the contact form page "form_fields" related name
class FormField(AbstractFormField):
    page = ParentalKey(
        "ContactFormPage",
        on_delete=models.CASCADE,
        related_name="form_fields",
    )


class ContactFormPage(WfCaptchaEmailForm):
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
