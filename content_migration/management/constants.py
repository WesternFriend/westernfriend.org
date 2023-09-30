DEFAULT_IMAGE_WIDTH: int = 350
DEFAULT_IMAGE_ALIGN: str | None = None

LOCAL_MIGRATION_DATA_DIRECTORY = "migration_data/"
SITE_BASE_URL = "https://westernfriend.org/"
WESTERN_FRIEND_LOGO_URL = "https://westernfriend.org/sites/default/files/logo-2020-%20transparency-120px_0.png"
WESTERN_FRIEND_LOGO_FILE_NAME = "logo-2020-%20transparency-120px_0.png"

# Although the keys are a bit redundant,
# they are used in at least one import script
# to get references to specific file names.
# The value is the file name to download and parse.
IMPORT_FILENAMES = {
    "archive_articles": "archive_articles.csv",
    "archive_issues": "archive_issues.csv",
    "board_documents": "board_documents.csv",
    "books": "books.csv",
    "civicrm_relationships": "CiviCRM_meeting_relationships.csv",
    "civicrm_contacts": "CiviCRM_Contacts.csv",
    "events": "events.csv",
    "extra_extra": "extra_extra.csv",
    "library_item_audience": "library_item_audience.csv",
    "library_item_genre": "library_item_genre.csv",
    "library_item_medium": "library_item_medium.csv",
    "library_item_time_period": "library_item_time_period.csv",
    "library_item_topic": "library_item_topic.csv",
    "library_items": "library_items.csv",
    "magazine_articles": "magazine_articles.csv",
    "magazine_authors": "magazine_authors.csv",
    "magazine_departments": "magazine_departments.csv",
    "magazine_issues": "magazine_issues.csv",
    "meeting_documents": "meeting_documents.csv",
    "memorials": "memorials.csv",
    "molly_wingate_blog": "molly_wingate.csv",
    "online_worship": "online_worship.csv",
    "pages": "pages.csv",
}
