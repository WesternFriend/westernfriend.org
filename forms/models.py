from django.db import models
from wagtail.core.fields import RichTextField
from wagtail.admin.edit_handlers import FieldPanel, InlinePanel
from wagtail.contrib.forms.models import AbstractForm, AbstractFormField
from wagtail.contrib.forms.edit_handlers import FormSubmissionsPanel

from modelcluster.fields import ParentalKey


class FormField(AbstractFormField):
    page = ParentalKey("ContactFormPage", on_delete=models.CASCADE,
                       related_name='form_fields')


class ContactFormPage(AbstractForm):
    intro = RichTextField(blank=True)
    thank_you_text = RichTextField(blank=True)

    content_panels = AbstractForm.content_panels + [
        FormSubmissionsPanel(),
        FieldPanel('intro', classname="full"),
        InlinePanel('form_fields', label="Form fields"),
        FieldPanel('thank_you_text', classname="full"),
    ]
