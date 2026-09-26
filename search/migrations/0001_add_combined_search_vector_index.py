# Adds the GIN expression index that Wagtail's PostgreSQL search backend needs.
#
# django-modelsearch (used by Wagtail's database search backend) filters with
# `(title || body) @@ to_tsquery(...)`. Its IndexEntry model says a computed
# GIN index on `title || body` is created in a SQL migration, but neither
# Wagtail nor modelsearch ships one, so every search did a sequential scan.
#
# Separate GIN indexes on `title` and `body` are not added here: Wagtail's
# 0006_customise_indexentry already creates them, and the planner can't use
# them for the concatenated expression anyway.

from django.db import migrations


class Migration(migrations.Migration):
    atomic = False  # Required for concurrent index creation

    dependencies = [
        ("wagtailsearch", "0006_customise_indexentry"),
    ]

    operations = [
        # The expression must match what modelsearch generates exactly
        # ("title" || "body") for the planner to use this index.
        migrations.RunSQL(
            sql="""
            CREATE INDEX CONCURRENTLY IF NOT EXISTS
            wagtailsearch_indexentry_title_body_gin_idx
            ON wagtailsearch_indexentry
            USING GIN ((title || body));
            """,
            reverse_sql="""
            DROP INDEX CONCURRENTLY IF EXISTS
            wagtailsearch_indexentry_title_body_gin_idx;
            """,
        ),
    ]
