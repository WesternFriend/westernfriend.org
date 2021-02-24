from django.db import models
from wagtail.core.fields import RichTextField
from wagtail.core.models import Orderable, Page
from wagtail.admin.edit_handlers import (
    FieldPanel,
    InlinePanel,
    PageChooserPanel
)
from wagtail.images.edit_handlers import ImageChooserPanel

from modelcluster.fields import (
    ParentalKey,
)

from cart.forms import CartAddProductForm


class StoreIndexPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
    ]

    parent_page_types = ["home.HomePage"]
    subpage_types = [
        "store.ProductIndexPage",
    ]

    max_count = 1

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request)

        context["products"] = Product.objects.all()
        context["cart_add_product_form"] = CartAddProductForm

        return context


class ProductIndexPage(Page):

    max_count = 1
    parent_page_types = [
        "store.StoreIndexPage",
    ]
    subpage_types = [
        "store.Book",
        #"store.Product",
    ]


class Product(Page):
    image = models.ForeignKey(
        "wagtailimages.Image", on_delete=models.SET_NULL, null=True, related_name="+"
    )
    description = RichTextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    available = models.BooleanField(default=True)

    parent_page_types = ["store.ProductIndexPage"]
    subpage_types = []

    content_panels = Page.content_panels + [
        FieldPanel("description", classname="full"),
        FieldPanel("price"),
        FieldPanel("available"),
        ImageChooserPanel("image"),
    ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request)

        context["cart_add_product_form"] = CartAddProductForm

        return context


class Book(Product):
    content_panels = Product.content_panels + [
        InlinePanel(
            "authors",
            heading="Authors",
            help_text="Select one or more authors, who contributed to this article",
        ),
    ]
    parent_page_types = [
        "store.ProductIndexPage",
    ]
    subpage_types = []


class BookAuthor(Orderable):
    book = ParentalKey(
        "store.Book",
        null=True,
        on_delete=models.CASCADE,
        related_name="authors",
    )
    author = models.ForeignKey(
        "wagtailcore.Page",
        null=True,
        on_delete=models.CASCADE,
        related_name="books_authored"
    )

    panels = [
        PageChooserPanel(
            "author",
            [
                "contact.Person",
                "contact.Meeting",
                "contact.Organization",
            ]
        )
    ]
