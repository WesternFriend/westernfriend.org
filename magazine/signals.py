from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from contact.models import ContactPublicationStatistics

from .models import ArchiveArticleAuthor, MagazineArticleAuthor


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
