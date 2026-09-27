from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.urls import reverse
from wagtail.contrib.frontend_cache.utils import PurgeBatch
from wagtail.models import Site
from wagtail.signals import page_published, page_unpublished, post_page_move

from contact.models import ContactPublicationStatistics

from .models import ArchiveArticleAuthor, MagazineArticle, MagazineArticleAuthor


@receiver(post_save, sender=MagazineArticleAuthor)
def update_contact_stats_on_magazine_article_change(sender, instance, **kwargs):
    """Update contact publication statistics when a magazine article author relationship is created or updated."""
    if instance.author:
        ContactPublicationStatistics.update_for_contact(instance.author)


@receiver(post_delete, sender=MagazineArticleAuthor)
def update_contact_stats_on_magazine_article_delete(sender, instance, **kwargs):
    """Update contact publication statistics when a magazine article author relationship is deleted."""
    if instance.author:
        ContactPublicationStatistics.update_for_contact(instance.author)


@receiver(post_save, sender=ArchiveArticleAuthor)
def update_contact_stats_on_archive_article_change(sender, instance, **kwargs):
    """Update contact publication statistics when an archive article author relationship is created or updated."""
    if instance.author:
        ContactPublicationStatistics.update_for_contact(instance.author)


@receiver(post_delete, sender=ArchiveArticleAuthor)
def update_contact_stats_on_archive_article_delete(sender, instance, **kwargs):
    """Update contact publication statistics when an archive article author relationship is deleted."""
    if instance.author:
        ContactPublicationStatistics.update_for_contact(instance.author)


@receiver(page_published, sender=MagazineArticle)
@receiver(page_unpublished, sender=MagazineArticle)
@receiver(post_page_move, sender=MagazineArticle)
@receiver(post_delete, sender=MagazineArticle)
def purge_ai_policy_files_on_article_change(sender, instance, **kwargs):
    """Purge robots.txt and llms.txt from Cloudflare when an article changes.

    Both files list the paths of articles excluded from AI use. Publishing
    can change the exclusion or the slug, and moving or removing an article
    changes its path, so the cached files would otherwise go stale until
    the edge TTL expires.
    """
    batch = PurgeBatch()
    for site in Site.objects.all():
        root_url = site.root_url.rstrip("/")
        batch.add_urls(
            f"{root_url}{reverse(name)}" for name in ("robots_txt", "llms_txt")
        )
    transaction.on_commit(batch.purge)
