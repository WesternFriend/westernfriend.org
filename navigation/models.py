from django.db import models

from wagtail.admin.edit_handlers import StreamFieldPanel
from wagtail.contrib.settings.models import BaseSetting, register_setting
from wagtail.core.fields import StreamField

from .blocks import (
    NavigationDropdownMenuBlock,
    NavigationExternalLinkBlock,
    NavigationPageChooserBlock,
)


@register_setting
class NavigationMenuSetting(BaseSetting):
    items = StreamField(
        [
            ("internal_page", NavigationPageChooserBlock()),
            ("external_link", NavigationExternalLinkBlock()),
            ("drop_down", NavigationDropdownMenuBlock()),
        ]
    )

    panels = [
        StreamFieldPanel("items"),
    ]

    class Meta:
        verbose_name = "Navigation menu"
