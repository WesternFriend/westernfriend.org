from django.db import models
from django.http import HttpRequest
from modelcluster.fields import ParentalKey  # type: ignore
from wagtail.admin.panels import FieldPanel, InlinePanel, PageChooserPanel
from wagtail.fields import RichTextField
from wagtail.models import Orderable, Page

from cart.forms import CartAddProductForm
from common.models import DrupalFields


class StoreIndexPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
    ]

    parent_page_types = ["home.HomePage"]
    subpage_types: list[str] = [
        "store.ProductIndexPage",
    ]

    max_count = 1

    def get_context(
        self,
        request: HttpRequest,
        *args: tuple,
        **kwargs: dict,
    ) -> dict:
        context = super().get_context(request)

        context["products"] = Product.objects.all()
        context["cart_add_product_form"] = CartAddProductForm

        return context


class ProductIndexPage(Page):
    max_count = 1
    parent_page_types = [
        "store.StoreIndexPage",
    ]
    subpage_types: list[str] = [
        "store.Book",
    ]


class Product(DrupalFields, Page):
    image = models.ForeignKey(
        "wagtailimages.Image",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,  # note, making this required will break the tests
        related_name="+",
    )
    description = RichTextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    available = models.BooleanField(default=True)

    parent_page_types = ["store.ProductIndexPage"]
    subpage_types: list[str] = []

    content_panels = Page.content_panels + [
        FieldPanel("description", classname="full"),
        FieldPanel("price"),
        FieldPanel("available"),
        FieldPanel("image"),
    ]

    def get_context(
        self,
        request: HttpRequest,
        *args: tuple,
        **kwargs: dict,
    ) -> dict:
        context = super().get_context(request)

        context["cart_add_product_form"] = CartAddProductForm

        return context


class Book(Product):  # type: ignore
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
    subpage_types: list[str] = []


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
        related_name="books_authored",
    )

    panels = [
        PageChooserPanel(
            "author", ["contact.Person", "contact.Meeting", "contact.Organization"]
        )
    ]
