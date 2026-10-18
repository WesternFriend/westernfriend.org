from wagtail.images.forms import BaseImageForm

DESCRIPTION_HELP_TEXT = (
    "Describe what the image shows, for people using a screen reader. "
    "Aim for a short sentence, and skip phrases like 'image of'."
)


class RequiredDescriptionImageForm(BaseImageForm):
    """Image form that requires a description.

    Templates use the description as alt text and fall back to the title, so an
    image saved without one leaves screen-reader users with filename-like alt
    text (WCAG 1.1.1). Wired up through the WAGTAILIMAGES_IMAGE_FORM_BASE
    setting, this applies to both the upload and edit forms in the admin.

    Images already stored without a description are left alone until someone
    edits them; `manage.py images_without_description` lists those.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        description = self.fields.get("description")
        if description is None:
            return

        description.required = True
        description.help_text = DESCRIPTION_HELP_TEXT
