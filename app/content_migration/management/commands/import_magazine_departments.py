import csv

import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from tqdm import tqdm

from magazine.models import MagazineDepartment, MagazineDepartmentIndexPage


class Command(BaseCommand):
    help = "Import Departments from Drupal site"

    def add_arguments(self, parser):
        parser.add_argument("--file", action="store", type=str)

    def handle(self, *args, **options):
        # Get the only instance of Magazine Department Index Page
        magazine_department_index_page = MagazineDepartmentIndexPage.objects.get()

        departments_list = pd.read_csv(options["file"]).to_dict("records")

        for department in tqdm(departments_list, desc="Departments", unit="row"):
            department_exists = MagazineDepartment.objects.filter(
                title=department["title"],
            ).exists()

            if not department_exists:
                import_department = MagazineDepartment(
                    title=department["title"],
                )

                # Add department to site page hiererchy
                magazine_department_index_page.add_child(instance=import_department)
                magazine_department_index_page.save()
