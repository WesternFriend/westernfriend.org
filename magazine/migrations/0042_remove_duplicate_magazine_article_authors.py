"""Remove duplicate article authors before the next migration forbids them.

An article could list the same contact as an author more than once, which
repeated the name on the page and in the feed and inflated publication
stats. The first entry, by sort order, is kept.

The constraint is added in its own migration: on PostgreSQL, deleting rows
and altering the same table in one transaction can fail with "pending
trigger events".
"""

from django.db import migrations
from django.db.models import Count, F


def first_entry_key(entry):
    """Sort key for the entry to keep: lowest sort order, then lowest id.

    Entries without a sort order go last, as the admin lists them last.
    """
    sort_order = entry.get("sort_order")
    return (sort_order is None, sort_order or 0, entry.get("pk") or 0)


def dedupe_author_entries(entries):
    """Return the author entries without repeats, keeping each first one."""
    kept = []
    seen = set()
    for entry in sorted(entries, key=first_entry_key):
        author = entry.get("author")
        if author is not None and author in seen:
            continue
        seen.add(author)
        kept.append(entry)
    return kept


def remove_duplicate_authors(apps, schema_editor):
    MagazineArticleAuthor = apps.get_model("magazine", "MagazineArticleAuthor")

    duplicated = (
        MagazineArticleAuthor.objects.values("article_id", "author_id")
        .annotate(rows=Count("id"))
        .filter(rows__gt=1)
    )
    for pair in duplicated:
        rows = MagazineArticleAuthor.objects.filter(
            article_id=pair["article_id"],
            author_id=pair["author_id"],
        ).order_by(F("sort_order").asc(nulls_last=True), "id")
        keep_id = rows.values_list("id", flat=True).first()
        rows.exclude(id=keep_id).delete()

    # Revisions store authors as JSON. Without this, publishing an old draft
    # or a scheduled revision would break the new constraint.
    Revision = apps.get_model("wagtailcore", "Revision")
    revisions = Revision.objects.filter(
        content_type__app_label="magazine",
        content_type__model="magazinearticle",
    )
    for revision in revisions.iterator():
        entries = revision.content.get("authors") or []
        kept = dedupe_author_entries(entries)
        if len(kept) != len(entries):
            revision.content["authors"] = kept
            revision.save(update_fields=["content"])


class Migration(migrations.Migration):
    dependencies = [
        ("wagtailcore", "0096_referenceindex_referenceindex_source_object_and_more"),
        ("magazine", "0041_alter_magazinearticle_body"),
    ]

    operations = [
        migrations.RunPython(
            remove_duplicate_authors,
            migrations.RunPython.noop,
        ),
    ]
