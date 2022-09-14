# Content migration

This document describes how to migrate existing content from Drupal to Wagtail.

## CiviCRM

CiviCRM stores contacts that are used in our Community Directory.

### Organizations (incl. meetings and worship groups)

1. Visit CiviCRM -> Search - Find Contacts
2. Set the search criteria to "is Organization"
   - this is because we only want organizations for our community directory
3. Click "search"
4. Click "Actions" -> "Export Contacts
5. Click "Select fields for export"
6. Choose "Organization export (mailing and worship)"
7. Click "Continue"
8. Click "Download File"
9. Open the CSV in LibreOffice and save it to fix the unicode issues with column names

Import the contacts with the following command.

```sh
python manage.py import_civicrm_contacts --file path/to/file.csv
```

### Addresses

Organization addresses can be imported with the same CSV downloaded in the previous section, by running the following command.

```py
python manage.py import_civicrm_addresses --file path/to/file.csv
```

### Relationships

1. Visit the CiviCRM [Relationships Report](https://westernfriend.org/civicrm/report/instance/5)
2. Click the "Filters" tab and select the following values for Contact Type A and Contact Type B
   - Yearly Meeting
   - Quarterly/Regional Meeting
   - Monthly Meeting
   - Worship Group
3. Click "View results"
4. Click "Actions" -> "Download CSV"
5. Name the file "CiviCRM_meeting_relationships.csv"
6. Open the file in LibreOffice and save it again as a CSV to fix the character encoding

Import the relationships with the following command.

```py
python manage.py import_civicrm_relationships --file path/to/file.csv
```

### Clerk relationships

TODO

## Magazine

The magazine is one of the most complicated features of this project. As such, it has several files that need to be migrated.

### Export

The Magazine data can be exported from the following URLs.

- [Authors](https://westernfriend.org/export/magazine_authors_uncleaned.csv)
- [Departments](https://westernfriend.org/export/magazine_departments.csv)
- [Issues](https://westernfriend.org/export/magazine_issues.csv)
- [Articles](https://westernfriend.org/export/magazine_articles.csv)

### Clean

The Magazine Authors data needs to be cleaned prior to import so

- author names can be separated correctly into given and family names
  - automatic separation by `parse_magazine_authors.py` in `content_migration` app merged carefully into online spreadsheet to avoid loss of previous manual work
  - manual review and cleaning by Mary via an online spreadsheet
- organizations can be categorized
- organizations with overlapping CiviCRM IDs can be identified

### Import

The Magazine data needs to be imported in a specific order, so that relationships will work properly.

1. Authors and Departments
2. Issues
3. Articles

The commands are as follows.Note: at some point, we may reduce this to a single command.

```sh
python manage.py import_magazine_authors --file /path/to/file
```

```sh
python manage.py import_magazine_departments --file /path/to/file
```

```sh
python manage.py import_magazine_issues --file /path/to/file
```

```sh
python manage.py import_magazine_articles --articles_file /path/to/file --authors_file /path/to/file
```
