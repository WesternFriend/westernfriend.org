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
#
# It also drops the indexes from the old search/migrations/0001_add_search_indexes,
# if any database has them. That migration never ran from main (the package had
# no __init__.py), and each of its indexes duplicated one that Django or
# Wagtail already creates.

from django.db import migrations

INDEX_NAME = "wagtailsearch_indexentry_title_body_gin_idx"

LEGACY_INDEX_NAMES = [
    "wagtailsearch_indexentry_content_type_id_idx",
    "wagtailsearch_indexentry_object_id_idx",
    "wagtailsearch_indexentry_title_gin_idx",
    "wagtailsearch_indexentry_body_gin_idx",
    "wagtailsearch_indexentry_content_type_object_id_idx",
]


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
            cursor.execute(
                "DROP INDEX CONCURRENTLY IF EXISTS "
                "wagtailsearch_indexentry_title_body_gin_idx",
            )

        # The expression must match what modelsearch generates exactly
        # ("title" || "body") for the planner to use this index.
        cursor.execute(
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS
            wagtailsearch_indexentry_title_body_gin_idx
            ON wagtailsearch_indexentry
            USING GIN ((title || body))
            """,
        )


def drop_index(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            "DROP INDEX CONCURRENTLY IF EXISTS "
            "wagtailsearch_indexentry_title_body_gin_idx",
        )


class Migration(migrations.Migration):
    atomic = False  # Required for concurrent index creation

    dependencies = [
        ("wagtailsearch", "0006_customise_indexentry"),
    ]

    operations = [
        migrations.RunPython(create_index, drop_index, atomic=False),
        *(
            migrations.RunSQL(
                sql=f"DROP INDEX CONCURRENTLY IF EXISTS {name}",
                # Not recreated on reverse: they duplicate existing indexes.
                reverse_sql=migrations.RunSQL.noop,
            )
            for name in LEGACY_INDEX_NAMES
        ),
    ]
