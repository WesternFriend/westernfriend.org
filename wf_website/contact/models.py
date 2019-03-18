from django.db import models
from wagtail.core.models import Page


class Contact(Page):
    class Meta:
        db_table = "contact"
