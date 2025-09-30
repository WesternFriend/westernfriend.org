# Content migration

This document describes how to migrate existing content from Drupal to Wagtail.

Note: if the import process fails for any reason, run the following commands

- `python manage.py reset_db -c` to completely reset the database (closing any sessions)
- `python manage.py migrate` to re-run migrations
- `python manage.py scaffold_initial_content` to prepare the initial content tree for data import

- [Content migration](#content-migration)
  - [Order matters](#order-matters)
  - [CiviCRM -\> Contacts, relationships, and clerks](#civicrm---contacts-relationships-and-clerks)
    - [Organizations (incl. meetings and worship groups)](#organizations-incl-meetings-and-worship-groups)
    - [Addresses](#addresses)
    - [Relationships](#relationships)
    - [Clerk relationships](#clerk-relationships)
  - [Magazine](#magazine)
    - [Export](#export)
    - [Clean](#clean)
    - [Import](#import)
      - [Single command](#single-command)
      - [Individual commands](#individual-commands)
  - [Media Library](#media-library)

## Order matters

Note the order of the imports is crucial. Specifically, be sure to import Drupal authors before CiviCRM contacts, since the CiviCRM contacts will cross-reference against Drupal authors.

The general import order should be:

1. Scaffold initial content
2. [Magazine content](#magazine)
   1. Departments
   2. Authors
   3. Issues
   4. Articles
3. [CiviCRM contacts/relationships](#civicrm---contacts-relationships-and-clerks)
4. [Media Library](#media-library)
   1. facets (there are multiple facets)
   2. Authors
   3. Items
5. Memorials

## Migration Data

The migration data need to reside in the `migration_data/` directory, or whatever directory is defined in `content_migration/management/constants.py` by the `LOCAL_MIGRATION_DATA_DIRECTORY`constant. Manually place the data in the local migration data directory, or use the download script described below.

### Download

The migration data can be kept in a remote or local folder. In the case of a remote folder, run the following command to place the migration data in the correct `migration_data/` directory.

```sh
python manage.py download_migration_data <http://url-to-data>
```

## CiviCRM -> Contacts, relationships, and clerks

CiviCRM stores contacts that are used in our Community Directory.

### Organizations (incl. meetings and worship groups)

1. Visit CiviCRM -> Search -> Find Contacts
2. Set the search criteria to "is Organization"
   - this is because we only want organizations for our community directory
3. Click "search"
4. select all records
5. Click "Actions" -> "Export Contacts
6. Click "Select fields for export"
7. Click "Use Saved Field Mapping" dropdown
8. Choose "Organization export (mailing and worship)"
9. Click "Continue"
10. Click "Download File"
11. Save the file as "CiviCRM_Contacts.csv" so it will work in the importer
12. Open the CSV in LibreOffice and save it to fix the Unicode issues with column names

Import the contacts with the following command.

```sh
python manage.py import_civicrm_contacts
```

### Relationships

1. Visit the CiviCRM [Relationships Report](https://westernfriend.org/civicrm/report/instance/5)
2. Click the "Filters" tab and select the following values for Contact Type A and Contact Type B
   - Yearly Meeting
   - Quarterly/Regional Meeting
   - Monthly Meeting
   - Worship Group
3. Click "View results"
4. Click "Actions" -> "Export as CSV"
5. Name the file "CiviCRM_meeting_relationships.csv"
6. Open the file in LibreOffice and save it again as a CSV to fix the character encoding

Import the relationships with the following command.

```sh
python manage.py import_civicrm_relationships
```

### Clerk relationships

1. Visit the CiviCRM [Relationships Report](https://westernfriend.org/civicrm/report/instance/5)
2. Click the "Filters" tab and
3. Select the following value for Contact Type A
   - Individual
4. Select the following values for Contact Type B
   - Yearly Meeting
   - Quarterly/Regional Meeting
   - Monthly Meeting
   - Worship Group
5. Select the relationship type "Is Presiding Clerk(s) of"
6. Select relationship status to Active
7. Click "View results"
8. Click "Actions" -> "Export as CSV"
9. Name the file "CiviCRM_clerk_relationships.csv"
10. Open the file in LibreOffice and save it again as a CSV to fix the character encoding

## Magazine

The magazine is one of the most complicated features of this project. As such, it has several files that need to be migrated.

### Export

The Magazine data can be exported from the following URLs.

- Authors: `/export/magazine_authors.csv`
- Departments: `/export/magazine_departments.csv`
- Issues: `/export/magazine_issues.csv`
- Articles: `/export/magazine_articles.csv`

### Import

The Magazine data needs to be imported in a specific order so that relationships will work properly.

1. Authors and Departments
2. Issues
3. Articles

#### Single command

Run this single command to import all magazine content in the correct order. Make sure all CSV files are in the same directory.

```sh
python manage.py import_magazine --data-directory /path/to/data/directory/
```

#### Individual commands

Below are the individual commands to import magazine content.

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

## Media Library

### Single command

Import all Library content with the following single command.

```sh
python manage.py import_library --folder /path/to/data/directory/
```

### Individual commands

Import the Media Library in the following order.

1. facets
2. authors
3. items

```sh
python manage.py import_library_item_facets --folder /path/to/files
```

```sh
python manage.py import_library_item_authors --file /path/to/file
```

```sh
python manage.py import_library_items --file /path/to/file
```

## Troubleshooting

### AttributeError: 'NoneType' object has no attribute '\_inc_path'

When encountering the `AttributeError: 'NoneType' object has no attribute '_inc_path'` error, run the following command:

```sh
python manage.py fixtree
```

See: https://stackoverflow.com/a/75327195/1191545
