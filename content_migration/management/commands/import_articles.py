
from django.core.management.base import BaseCommand, CommandError
import numpy as np
import pandas as pd

from taggit.models import Tag

from magazine.models import MagazineArticle, MagazineArticleAuthor, MagazineArticleTag, MagazineDepartment, MagazineIssue

from contact.models import (
    Meeting,
    Organization,
    Person
)


class Command(BaseCommand):
    help = "Import Articles from Drupal site while linking them to Authors, Issues, Deparments, and Keywords"

    def add_arguments(self, parser):
        parser.add_argument("--articles_file", action="store", type=str)
        # parser.add_argument("--authors_file", action="store", type=str)

    def handle(self, *args, **options):
        articles = pd.read_csv(options["articles_file"])
        authors = pd.read_csv("../wf_import_Data/authors_cleaned_deduped-2020-04-12.csv")

        for index, row in articles.iterrows():
            # Example article
            # title                                         Quaker Culture: Simplicity
            # Authors                                      Philadelphia Yearly Meeting
            # Department                                                Quaker Culture
            # Keywords                                              Simplicity, Beauty
            # Media                                                                NaN
            # related_issue_title                                               On Art
            # Body

            department = MagazineDepartment.objects.get(title=row["Department"])

            article = MagazineArticle(
                title=row["title"],
                body_migrated=row["Body"],
                department=department
            )

            try:
                related_issue = MagazineIssue.objects.get(title=row["related_issue_title"])
            except:
                print("Can't find issue: ", row["related_issue_title"])
                print(row)

            related_issue.add_child(instance=article)

            for author in row["Authors"].split(", "):
                authors_mask = authors["drupal_full_name"] == author
                author_data = authors[authors_mask].iloc[0].to_dict()

                if author_data["organization_name"] is not np.nan:
                    author = Organization.objects.get(drupal_full_name=author_data["drupal_full_name"])
                elif author_data["meeting_name"] is not np.nan:
                    author = Meeting.objects.get(drupal_full_name=author_data["drupal_full_name"])
                else:
                    author = Person.objects.get(drupal_full_name=author_data["drupal_full_name"])

                article_author = MagazineArticleAuthor(article=article, author=author)
                article.authors.add(article_author)
            try:
                for keyword in row["Keywords"].split(", "):
                    article.tags.add(keyword)
            except:
                print("could not split: '", row["Keywords"], "'")

            article.save()