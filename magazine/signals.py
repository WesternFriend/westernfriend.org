from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from wagtail.models import Site
from wagtail.signals import page_published, page_unpublished, post_page_move

from common.signal_handlers import purge_crawler_files
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


@receiver(page_published)
@receiver(page_unpublished)
@receiver(post_page_move)
def purge_ai_policy_files_on_page_change(sender, instance, **kwargs):
    """Purge robots.txt and llms.txt from Cloudflare when an article changes.

    Both files list the paths of articles excluded from AI use. Publishing
    an article can change the exclusion or the slug. Publishing, moving or
    unpublishing an article or one of its ancestors, such as its issue,
    changes or removes its path. The cached files would otherwise go stale
    until the edge TTL expires.
    """
    if (
        isinstance(instance, MagazineArticle)
        or MagazineArticle.objects.descendant_of(instance)
        .filter(exclude_from_ai=True)
        .exists()
    ):
        purge_crawler_files(Site.objects.all())


@receiver(post_delete, sender=MagazineArticle)
def purge_ai_policy_files_on_article_delete(sender, instance, **kwargs):
    """Purge robots.txt and llms.txt when an article is deleted."""
    purge_crawler_files(Site.objects.all())
