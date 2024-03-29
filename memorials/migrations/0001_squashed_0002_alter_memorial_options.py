# Generated by Django 4.2.1 on 2023-05-24 06:04

from django.db import migrations, models
import django.db.models.deletion
import wagtail.fields


class Migration(migrations.Migration):
    replaces = [
        ("memorials", "0001_initial"),
        ("memorials", "0002_alter_memorial_options"),
    ]

    initial = True

    dependencies = [
        ("wagtailcore", "0066_collection_management_permissions"),
        ("contact", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="MemorialIndexPage",
            fields=[
                (
                    "page_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="wagtailcore.page",
                    ),
                ),
                ("intro", wagtail.fields.RichTextField(blank=True)),
            ],
            options={
                "abstract": False,
            },
            bases=("wagtailcore.page",),
        ),
        migrations.CreateModel(
            name="Memorial",
            fields=[
                (
                    "page_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="wagtailcore.page",
                    ),
                ),
                ("date_of_birth", models.DateField(blank=True, null=True)),
                ("date_of_death", models.DateField(blank=True, null=True)),
                ("dates_are_approximate", models.BooleanField(default=False)),
                ("memorial_minute", wagtail.fields.RichTextField(blank=True)),
                (
                    "drupal_memorial_id",
                    models.PositiveIntegerField(blank=True, null=True),
                ),
                (
                    "memorial_meeting",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="memorial_minutes",
                        to="contact.meeting",
                    ),
                ),
                (
                    "memorial_person",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="memorial_minute",
                        to="contact.person",
                    ),
                ),
            ],
            options={
                "abstract": False,
                "ordering": (
                    "memorial_person__family_name",
                    "memorial_person__given_name",
                ),
            },
            bases=("wagtailcore.page",),
        ),
    ]
