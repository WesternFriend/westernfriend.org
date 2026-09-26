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

INDEX_NAME = "wagtailsearch_indexentry_title_body_gin_idx"


def create_index(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        # An interrupted CREATE INDEX CONCURRENTLY leaves an invalid index
        # behind under the same name, which IF NOT EXISTS would then skip.
        cursor.execute(
            """
            SELECT NOT i.indisvalid
            FROM pg_index i
            JOIN pg_class c ON c.oid = i.indexrelid
            WHERE c.relname = %s
            """,
            [INDEX_NAME],
        )
        row = cursor.fetchone()
        if row and row[0]:
            cursor.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {INDEX_NAME}")

        # The expression must match what modelsearch generates exactly
        # ("title" || "body") for the planner to use this index.
        cursor.execute(
            f"""
            CREATE INDEX CONCURRENTLY IF NOT EXISTS {INDEX_NAME}
            ON wagtailsearch_indexentry
            USING GIN ((title || body))
            """,
        )


def drop_index(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {INDEX_NAME}")


class Migration(migrations.Migration):
    atomic = False  # Required for concurrent index creation

    dependencies = [
        ("wagtailsearch", "0006_customise_indexentry"),
    ]

    operations = [
        migrations.RunPython(create_index, drop_index, atomic=False),
    ]
