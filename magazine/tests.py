import datetime
from django.test import TestCase
from wagtail.models import Page, Site
from home.models import HomePage
from .models import (
    MagazineDepartmentIndexPage,
    MagazineDepartment,
    MagazineIssue,
    MagazineIndexPage,
    MagazineArticle,
)


class MagazineIssueTest(TestCase):
    def setUp(self) -> None:
        site_root = Page.objects.get(id=2)

        self.home_page = HomePage(title="Home")
        site_root.add_child(instance=self.home_page)

        Site.objects.all().update(root_page=self.home_page)

        self.magazine_index = MagazineIndexPage(title="Magazine")
        self.home_page.add_child(instance=self.magazine_index)

        self.magazine_issue = MagazineIssue(
            title="Issue 1",
            issue_number=1,
            publication_date="2020-01-01",
        )

        self.magazine_department_index = MagazineDepartmentIndexPage(
            title="Departments",
        )
        self.magazine_index.add_child(instance=self.magazine_department_index)
        self.magazine_department = MagazineDepartment(
            title="Department 1",
        )
        self.magazine_department_index.add_child(instance=self.magazine_department)

        self.magazine_index.add_child(instance=self.magazine_issue)
        self.magazine_article_one = self.magazine_issue.add_child(
            instance=MagazineArticle(
                title="Article 1",
                department=self.magazine_department,
                is_featured=True,
            ),
        )
        self.magazine_article_two = self.magazine_issue.add_child(
            instance=MagazineArticle(
                title="Article 2",
                department=self.magazine_department,
                is_featured=False,
            ),
        )

    def test_featured_articles(self) -> None:
        """Test that the featured_articles property returns the correct
        articles."""
        self.assertEqual(
            list(self.magazine_issue.featured_articles),
            [self.magazine_article_one],
        )

    def test_publication_end_date(self) -> None:
        """Test that the publication_end_date property returns the correct
        date."""
        self.assertEqual(
            self.magazine_issue.publication_end_date,
            datetime.date(2020, 2, 1),
        )

    def test_get_context(self) -> None:
        # Here you would add tests for the get_context method.
        pass

    def test_get_sitemap_urls(self) -> None:
        # Here you would add tests for the get_sitemap_urls method.
        pass
