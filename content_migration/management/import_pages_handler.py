from tqdm import tqdm
from content_migration.management.shared import parse_csv_file

from home.models import HomePage
from news.models import NewsIndexPage


def handle_import_pages(file_name: str) -> None:
    # Get references to relevant index pages
    HomePage.objects.get()
    NewsIndexPage.objects.get()

    pages = parse_csv_file(file_name)

    for page in tqdm(
        pages,
        total=len(pages),
        desc="Pages",
        unit="row",
    ):
        pass
