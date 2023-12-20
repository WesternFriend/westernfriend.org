from wagtail import hooks
from .models import Meeting, Organization, Person


@hooks.register("construct_queryset")
def prefetch_contact_related(queryset):
    """Prefetch related objects for contact models."""
    contact_models = [Meeting, Organization, Person]
    if queryset.model in contact_models:
        return queryset.prefetch_related(
            "articles_authored__article",
            "archive_articles_authored__article",
            "library_items_authored__library_item",
            "memorial_minutes__memorial_person",
            "presiding_clerks__person",
        )

    return queryset
