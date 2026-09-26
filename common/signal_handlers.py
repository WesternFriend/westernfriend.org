from django.db import transaction
from django.db.models.signals import post_delete, post_save
from wagtail.contrib.frontend_cache.utils import PurgeBatch
from wagtail.models import PageViewRestriction


def purge_restricted_pages(instance, **kwargs):
    """Purge a page and its descendants from Cloudflare when access changes.

    Wagtail purges pages on publish and unpublish only. Adding a view
    restriction to a page Cloudflare has cached would otherwise leave its
    public copy served to anonymous visitors until the edge TTL expires.
    A restriction covers the page's whole subtree, so purge all of it.
    """
    page = instance.page
    batch = PurgeBatch()
    batch.add_pages(page.get_descendants(inclusive=True).live().specific())

    # Purge after commit, so no request re-caches the old public page
    # between the purge and the restriction becoming visible.
    transaction.on_commit(batch.purge)


def register_signal_handlers():
    for signal in (post_save, post_delete):
        signal.connect(
            purge_restricted_pages,
            sender=PageViewRestriction,
            dispatch_uid=f"purge_restricted_pages_{signal is post_save}",
        )
