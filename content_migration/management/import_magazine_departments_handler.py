from tqdm import tqdm
from content_migration.management.shared import parse_csv_file

from magazine.models import MagazineDepartment, MagazineDepartmentIndexPage


def handle_import_magazine_departments(file_name: str) -> None:
    # Get the only instance of Magazine Department Index Page
    magazine_department_index_page = MagazineDepartmentIndexPage.objects.get()

    departments_list = parse_csv_file(file_name)

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
