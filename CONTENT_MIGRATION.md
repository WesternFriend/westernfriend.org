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
6. Choose "Organization - primary fields"
7. Click "Continue"
8. Click "Download File"

Import the contacts with the following command.

```sh
python manage.py import_civicrm_contacts --file path/to/file.csv
```

### Addresses

### Relationships

1. Visit the CiviCRM [Relationships Report](https://westernfriend.org/civicrm/report/instance/5)
2. Click "Actions" -> "Download CSV"
3. Name the file "CiviCRM_relationships.csv"

### Clerk relationships
