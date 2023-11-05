from wagtail.models import Page


def get_or_create_site_root_page() -> Page:
    root_page: Page
    try:
        root_page = Page.objects.get(
            id=1,
        )
    except Page.DoesNotExist:
        root_page = Page.objects.create(
            id=1,
        ).save()

    return root_page
