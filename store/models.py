from django.db import models
from wagtail.core.fields import RichTextField
from wagtail.core.models import Page
from wagtail.admin.edit_handlers import FieldPanel
from wagtail.images.edit_handlers import ImageChooserPanel


class StoreIndexPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
    ]

    subpage_types = [
        "store.CategoryIndexPage",
        "store.ProductIndexPage",
    ]

    max_count = 1

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request)

        context["products"] = Product.objects.all()

        return context


class CategoryIndexPage(Page):

    max_count = 1

    subpage_types = [
        "store.Category",
    ]


class Category(Page):

    subpage_types = []

    class Meta:
        verbose_name = "category"
        verbose_name_plural = "categories"


class ProductIndexPage(Page):

    max_count = 1

    subpage_types = [
        "store.Product",
    ]


class Product(Page):
    product_category = models.ForeignKey(
        to="store.Category",
        related_name="products",
        on_delete=models.PROTECT,
    )
    image = models.ForeignKey(
        "wagtailimages.Image", on_delete=models.SET_NULL, null=True, related_name="+"
    )
    description = RichTextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    available = models.BooleanField(default=True)

    content_panels = Page.content_panels + [
        FieldPanel("description", classname="full"),
        FieldPanel("product_category"),
        FieldPanel("price"),
        FieldPanel("available"),
        ImageChooserPanel("image"),
    ]
