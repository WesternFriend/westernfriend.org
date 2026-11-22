"""The same contact can't be an author of one magazine article twice."""

import importlib

from django.apps import apps as django_apps
from django.db import IntegrityError, connection, transaction
from django.test import TestCase
from django.urls import reverse
from wagtail.test.utils.form_data import (
    inline_formset,
    nested_form_data,
    rich_text,
    streamfield,
)

from accounts.models import User
from contact.factories import PersonFactory
from contact.models import ContactPublicationStatistics
from magazine.factories import MagazineArticleFactory, MagazineIssueFactory
from magazine.feeds import MagazineArticleFeed
from magazine.models import ArchiveArticle, ArchiveArticleAuthor, MagazineArticleAuthor

cleanup = importlib.import_module(
    "magazine.migrations.0042_remove_duplicate_magazine_article_authors",
)


class DuplicateAuthorTestCase(TestCase):
    def setUp(self):
        self.issue = MagazineIssueFactory.create()
        self.article = MagazineArticleFactory.create(parent=self.issue)
        self.person = PersonFactory.create()
        self.other_person = PersonFactory.create()

    def drop_constraint(self):
        """Allow duplicates as they were before the constraint.

        PostgreSQL DDL is transactional, so the test's rollback restores it.
        """
        constraint = next(
            c
            for c in MagazineArticleAuthor._meta.constraints
            if c.name == "unique_magazine_article_author"
        )
        with connection.schema_editor() as editor:
            editor.remove_constraint(MagazineArticleAuthor, constraint)


class UniqueConstraintTest(DuplicateAuthorTestCase):
    def test_database_rejects_duplicate_author(self):
        MagazineArticleAuthor.objects.create(article=self.article, author=self.person)
        with self.assertRaises(IntegrityError), transaction.atomic():
            MagazineArticleAuthor.objects.create(
                article=self.article,
                author=self.person,
            )

    def test_revision_with_distinct_authors_publishes(self):
        self.article.authors.add(
            MagazineArticleAuthor(author=self.person),
            MagazineArticleAuthor(author=self.other_person),
        )
        self.article.save_revision().publish()
        self.article.save_revision().publish()

        self.assertEqual(self.article.authors.count(), 2)


class CleanupMigrationTest(DuplicateAuthorTestCase):
    def test_keeps_first_entry_by_sort_order(self):
        self.drop_constraint()
        later = MagazineArticleAuthor.objects.create(
            article=self.article,
            author=self.person,
            sort_order=2,
        )
        first = MagazineArticleAuthor.objects.create(
            article=self.article,
            author=self.person,
            sort_order=0,
        )
        unsorted = MagazineArticleAuthor.objects.create(
            article=self.article,
            author=self.person,
            sort_order=None,
        )
        other = MagazineArticleAuthor.objects.create(
            article=self.article,
            author=self.other_person,
            sort_order=1,
        )

        cleanup.remove_duplicate_authors(django_apps, None)

        remaining = set(
            MagazineArticleAuthor.objects.filter(article=self.article).values_list(
                "id",
                flat=True,
            ),
        )
        self.assertEqual(remaining, {first.id, other.id})
        self.assertNotIn(later.id, remaining)
        self.assertNotIn(unsorted.id, remaining)

    def test_removes_duplicates_from_revisions(self):
        revision = self.article.save_revision()
        revision.content["authors"] = [
            {"pk": 11, "author": self.person.id, "sort_order": 1},
            {"pk": 10, "author": self.person.id, "sort_order": 0},
            {"pk": 12, "author": self.other_person.id, "sort_order": 2},
        ]
        revision.save(update_fields=["content"])

        cleanup.remove_duplicate_authors(django_apps, None)

        revision.refresh_from_db()
        self.assertEqual(
            [entry["pk"] for entry in revision.content["authors"]],
            [10, 12],
        )

    def test_leaves_revisions_without_duplicates_alone(self):
        entries = [
            {"pk": 11, "author": self.other_person.id, "sort_order": 1},
            {"pk": 10, "author": self.person.id, "sort_order": 0},
        ]
        revision = self.article.save_revision()
        revision.content["authors"] = entries
        revision.save(update_fields=["content"])

        cleanup.remove_duplicate_authors(django_apps, None)

        revision.refresh_from_db()
        self.assertEqual(revision.content["authors"], entries)


class ArticleFormTest(DuplicateAuthorTestCase):
    def setUp(self):
        super().setUp()
        admin = User.objects.create_superuser(email="admin@example.com", password=None)
        self.client.force_login(admin)

    def post_authors(self, *author_ids):
        data = nested_form_data(
            {
                "title": self.article.title,
                "slug": self.article.slug,
                "teaser": rich_text("<p>Teaser</p>"),
                "body": streamfield(
                    [("rich_text", rich_text("<p>Body</p>"))],
                ),
                "authors": inline_formset(
                    [{"author": author_id} for author_id in author_ids],
                    min=1,
                ),
                "department": self.article.department_id,
                "tags": "",
            },
        )
        return self.client.post(
            reverse("wagtailadmin_pages:edit", args=[self.article.id]),
            data,
        )

    def test_rejects_duplicate_author_with_message(self):
        response = self.post_authors(self.person.id, self.person.id)

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            f"{self.person} is already an author of this article.",
        )
        self.assertFalse(self.article.authors.exists())

    def test_accepts_distinct_authors(self):
        response = self.post_authors(self.person.id, self.other_person.id)

        self.assertEqual(response.status_code, 302)
        self.article.refresh_from_db()
        latest = self.article.get_latest_revision_as_object()
        self.assertEqual(
            [link.author_id for link in latest.authors.all()],
            [self.person.id, self.other_person.id],
        )


class DistinctCountsTest(DuplicateAuthorTestCase):
    def test_stats_count_an_article_once(self):
        self.drop_constraint()
        MagazineArticleAuthor.objects.create(article=self.article, author=self.person)
        MagazineArticleAuthor.objects.create(article=self.article, author=self.person)

        ContactPublicationStatistics.update_for_contact(self.person)

        stats = ContactPublicationStatistics.objects.get(contact=self.person)
        self.assertEqual(stats.article_count, 1)

    def test_stats_count_each_distinct_article(self):
        second = MagazineArticleFactory.create(parent=self.issue)
        MagazineArticleAuthor.objects.create(article=self.article, author=self.person)
        MagazineArticleAuthor.objects.create(article=second, author=self.person)
        archive_article = ArchiveArticle.objects.create(title="Archive article")
        ArchiveArticleAuthor.objects.create(
            article=archive_article,
            author=self.person,
        )

        ContactPublicationStatistics.update_for_contact(self.person)

        stats = ContactPublicationStatistics.objects.get(contact=self.person)
        self.assertEqual(stats.article_count, 3)

    def test_feed_names_each_author_once(self):
        self.drop_constraint()
        for author in (self.person, self.other_person, self.person):
            MagazineArticleAuthor.objects.create(article=self.article, author=author)

        name = MagazineArticleFeed().item_author_name(self.article)

        self.assertEqual(name, f"{self.person}, {self.other_person}")
