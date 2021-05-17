import csv

from tqdm import tqdm

from django.core.management.base import BaseCommand, CommandError

from magazine.models import MagazineDepartment, MagazineDepartmentIndexPage


class Command(BaseCommand):
    help = "Import Departments from Drupal site"

    def add_arguments(self, parser):
        parser.add_argument("--file", action="store", type=str)

    def handle(self, *args, **options):
        # Get the only instance of Magazine Department Index Page
        magazine_department_index_page = MagazineDepartmentIndexPage.objects.get()

        with open(options["file"]) as import_file:
            departments = csv.DictReader(import_file)
            departments_list = list(departments)

            for department in tqdm(departments_list, desc="Departments", unit="row"):
                import_department = MagazineDepartment(
                    title=department["title"],
                )

                # Add department to site page hiererchy
                magazine_department_index_page.add_child(instance=import_department)
                magazine_department_index_page.save()

        self.stdout.write("All done!")
