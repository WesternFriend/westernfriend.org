from urllib.parse import urlsplit

from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.urls import reverse
from wagtail.contrib.frontend_cache.utils import PurgeBatch
from wagtail.models import PageViewRestriction, Site
from wagtail.signals import page_published, page_unpublished, post_page_move

from common.models import CrawlerPolicySetting


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


def purge_crawler_files(sites):
    """Purge robots.txt and llms.txt for the given sites, after commit."""
    # Site.root_url says http:// for a port 80 site, but crawlers fetch these
    # files over HTTPS, so use the public scheme to purge the cached copies.
    scheme = urlsplit(settings.BASE_URL).scheme
    batch = PurgeBatch()
    for site in sites:
        root_url = f"{scheme}://{urlsplit(site.root_url).netloc}"
        batch.add_urls(
            f"{root_url}{reverse(name)}" for name in ("robots_txt", "llms_txt")
        )
    transaction.on_commit(batch.purge)


def purge_crawler_policy_files(instance, **kwargs):
    """Purge robots.txt and llms.txt from Cloudflare when the policy changes.

    Both files are cached at the edge like any public page, so without a
    purge a changed crawler policy would wait for the edge TTL to expire.
    """
    purge_crawler_files([instance.site])


def purge_live_page_url_cache(page):
    """Drop the cached footer URL for this page's slug, on every site.

    ``live_page_url_by_slug`` caches the URL per (site, slug) so the footer
    costs no query once warm. Without this, unpublishing, moving, or restricting
    the linked page would leave its old URL in the footer — and so a dead or
    404 link — until the cache's TTL expired. Clearing every site's key for the
    slug is cheap (sites are few and Wagtail caches them) and covers whichever
    site the page belongs to.

    Honest limit: this keys off the page's *current* slug, so renaming a
    live page's slug is only reflected within LIVE_PAGE_URL_CACHE_SECONDS;
    publish, unpublish, move, and privacy changes are reflected at once.
    """
    # Imported lazily so this module (loaded in AppConfig.ready) does not import
    # the template tag library at app-registry setup time.
    from common.templatetags.common_tags import live_page_url_cache_key

    keys = [live_page_url_cache_key(None, page.slug)]
    keys += [
        live_page_url_cache_key(site_id, page.slug)
        for site_id in Site.objects.values_list("id", flat=True)
    ]
    # Delete after commit, so a concurrent footer request cannot re-read the
    # pre-commit page state and re-cache it between this purge and the change
    # becoming visible (which would hide the link after a publish, or keep a
    # dead link after an unpublish, for the cache's TTL).
    transaction.on_commit(lambda: cache.delete_many(keys))


def purge_live_page_url_for_page(instance, **kwargs):
    """page_published / page_unpublished / post_page_move handler."""
    purge_live_page_url_cache(instance)


def purge_live_page_url_for_restriction(instance, **kwargs):
    """PageViewRestriction handler — privacy changes alter .public() results."""
    purge_live_page_url_cache(instance.page)


def register_signal_handlers():
    for signal in (post_save, post_delete):
        # Deleting a saved policy returns the site to the defaults
        signal.connect(
            purge_crawler_policy_files,
            sender=CrawlerPolicySetting,
            dispatch_uid=f"purge_crawler_policy_files_{signal is post_save}",
        )
        signal.connect(
            purge_restricted_pages,
            sender=PageViewRestriction,
            dispatch_uid=f"purge_restricted_pages_{signal is post_save}",
        )
        signal.connect(
            purge_live_page_url_for_restriction,
            sender=PageViewRestriction,
            dispatch_uid=f"purge_live_page_url_restriction_{signal is post_save}",
        )

    for wagtail_signal, uid in (
        (page_published, "purge_live_page_url_on_publish"),
        (page_unpublished, "purge_live_page_url_on_unpublish"),
        (post_page_move, "purge_live_page_url_on_move"),
    ):
        wagtail_signal.connect(purge_live_page_url_for_page, dispatch_uid=uid)
