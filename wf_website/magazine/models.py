from django.db import models

from wagtail.admin.edit_handlers import FieldPanel
from wagtail.core.models import Page
from wagtail.core.fields import RichTextField
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.search import index
from wagtail.snippets.edit_handlers import SnippetChooserPanel
from wagtail.snippets.models import register_snippet


class MagazineIndexPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel('intro')
    ]

    subpage_types = [
        'MagazineIssue',
    ]


class MagazineIssue(Page):
    cover_image = models.ForeignKey(
        'wagtailimages.Image',
        on_delete=models.SET_NULL,
        null=True,
        related_name='+',
    )
    publication_date = models.DateField(
        null=True,
    )

    content_panels = Page.content_panels + [
        FieldPanel('publication_date'),
        ImageChooserPanel('cover_image'),
    ]

    subpage_types = [
        'MagazineArticle',
    ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request)

        context['articles_by_department'] = MagazineArticle.objects.child_of(self).live().order_by('department__name')

        return context


class MagazineArticle(Page):
    body = RichTextField(blank=True)
    department = models.ForeignKey(
        'MagazineDepartment',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )

    search_fields = Page.search_fields + [
        index.SearchField('body'),
    ]

    content_panels = Page.content_panels + [
        FieldPanel('body', classname="full"),
        SnippetChooserPanel('department'),
    ]

    subpage_types = []


@register_snippet
class MagazineDepartment(models.Model):
    name = models.CharField(max_length=200)

    panels = [
        FieldPanel('name')
    ]

    def __str__(self):
        return self.name