
from django.core.management.base import BaseCommand, CommandError
import pandas as pd

from magazine.models import MagazineArticle, MagazineIssue

from contact.models import (
    Meeting,
    Organization,
    Person
)


class Command(BaseCommand):
    help = "Import Articles from Drupal site while linking them to Authors, Issues, Deparments, and Keywords"

    def add_arguments(self, parser):
        parser.add_argument("--articles_file", action="store", type=str)
        #parser.add_argument("--authors_file", action="store", type=str)

    def handle(self, *args, **options):
        articles = pd.read_csv(options["articles_file"])
        # authors = pd.read_csv("../wf_import_Data/authors_cleaned_deduped-2020-04-12.csv", index_col="drupal_full_name")

        for index, row in articles[:3].iterrows():
            # Example article
            # title                                         Quaker Culture: Simplicity
            # Authors                                      Philadelphia Yearly Meeting
            # Department                                                Quaker Culture
            # Keywords                                              Simplicity, Beauty
            # Media                                                                NaN
            # related_issue_title                                               On Art
            # Body

            article = MagazineArticle(
                title=row["title"]
            )

            related_issue = MagazineIssue.objects.get(title=row["related_issue_title"])

            related_issue.add_child(instance=article)
            # related_issue.save

            # for author in article["Authors"].split(", "):
            #     authors_mask = authors.index == "Mary Klein"
            #     authors[authors_mask].iloc[0].to_dict()
