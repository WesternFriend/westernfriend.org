# Content migration

This document describes how to migrate existing content from Drupal to Wagtail.

Note: if the import process fails for any reason, run the following commands

- `python manage.py reset_db` to completely reset the database
- `python manage.py migrate` to re-run migrations
- `python manage.py scaffold_initial_content` to prepare the initial content tree for data import

- [Content migration](#content-migration)
  - [Order matters](#order-matters)
  - [Pre-processing](#pre-processing)
    - [Magazine Authors -\> Contacts](#magazine-authors---contacts)
    - [Library Item Authors -\> Contacts](#library-item-authors---contacts)
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

## Pre-processing

Some data must be pre-processed and manually cleaned prior to import.

### Magazine Authors -> Contacts

Magazine Authors are stored as a Drupal taxonomy, with only a `drupal_full_name` field for people, meetings, and organizations.

We must pre-process the Magazine Authors as follows.

1. use a script to separate the author names into `given_name` and `family_names` fields
2. manually review the authors to ensure the names were split correctly
3. identify meetings and organizations by filling in a `meeting_name` and `organization_name` respectively in the final spreadsheet

To preserve work, subsequent iterations should be processed as follows.

1. use a script to separate the author names into `given_name` and `family_name` fields
2. use a script to merge only **new** authors into the existing spreadsheet by ignoring existing `drupal_author_id`s
3. manually review the authors to ensure the names were split correctly
4. identify meetings and organizations by filling in a `meeting_name` and `organization_name` respectively in the final spreadsheet

### Library Item Authors -> Contacts

Library Item authors have only a `drupal_full_name` field. They should be processed and merged into the Contacts as follows.

1. use a script to separate the author names into `given_name` and `family_name` fields
2. use a script to merge only **new** authors into the existing spreadsheet by ignoring existing `drupal_author_id`s
3. manually review the authors to ensure the names were split correctly
4. identify meetings and organizations by filling in a `meeting_name` and `organization_name` respectively in the final spreadsheet

## CiviCRM -> Contacts, relationships, and clerks

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
9. Open the CSV in LibreOffice and save it to fix the Unicode issues with column names

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

- Authors: `/export/magazine_authors_uncleaned.csv`
- Departments: `/export/magazine_departments.csv`
- Issues: `/export/magazine_issues.csv`
- Articles: `/export/magazine_articles.csv`

### Clean

The Magazine Authors' data needs to be cleaned prior to import so

- author names can be separated correctly into given and family names
  - automatic separation by `parse_magazine_authors.py` in `content_migration` app merged carefully into an online spreadsheet to avoid loss of previous manual work
  - manual review and cleaning by Mary via an online spreadsheet
- organizations can be categorized
- organizations with overlapping CiviCRM IDs can be identified

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
