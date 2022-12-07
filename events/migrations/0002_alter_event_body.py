# Generated by Django 3.2.13 on 2022-05-23 07:32

import re

import django.core.validators
import wagtail.core.blocks
import wagtail.core.fields
import wagtail.images.blocks
import wagtail_color_panel.blocks
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="event",
            name="body",
            field=wagtail.core.fields.StreamField(
                [
                    (
                        "heading",
                        wagtail.core.blocks.StructBlock(
                            [
                                (
                                    "heading_level",
                                    wagtail.core.blocks.ChoiceBlock(
                                        choices=[
                                            ("h2", "Level 2 (child of level 1)"),
                                            ("h3", "Level 3 (child of level 2)"),
                                            ("h4", "Level 4 (child of level 3)"),
                                            ("h5", "Level 5 (child of level 4)"),
                                            ("h6", "Level 6 (child of level 5)"),
                                        ],
                                        help_text="These different heading levels help to communicate the organization and hierarchy of the content on a page.",
                                    ),
                                ),
                                (
                                    "heading_text",
                                    wagtail.core.blocks.CharBlock(
                                        help_text="The text to appear in the heading."
                                    ),
                                ),
                                (
                                    "target_slug",
                                    wagtail.core.blocks.CharBlock(
                                        help_text="Used to link to a specific location within this page. A slug should only contain letters, numbers, underscore (_), or hyphen (-).",
                                        required=False,
                                        validators=(
                                            django.core.validators.RegexValidator(
                                                re.compile("^[-a-zA-Z0-9_]+\\Z"),
                                                "Enter a valid “slug” consisting of letters, numbers, underscores or hyphens.",
                                                "invalid",
                                            ),
                                        ),
                                    ),
                                ),
                                (
                                    "color",
                                    wagtail_color_panel.blocks.NativeColorBlock(
                                        required=False
                                    ),
                                ),
                            ]
                        ),
                    ),
                    ("rich_text", wagtail.core.blocks.RichTextBlock()),
                    (
                        "image",
                        wagtail.core.blocks.StructBlock(
                            [
                                ("image", wagtail.images.blocks.ImageChooserBlock()),
                                (
                                    "width",
                                    wagtail.core.blocks.IntegerBlock(
                                        help_text="Enter the desired image width value in pixels up to 800 max.",
                                        max_value=800,
                                        min_value=0,
                                    ),
                                ),
                            ]
                        ),
                    ),
                ],
                blank=True,
                null=True,
            ),
        ),
    ]
