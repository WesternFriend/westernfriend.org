# Content migration

This document describes how to migrate existing content from Drupal to Wagtail.

## CiviCRM (contacts)

CiviCRM stores contacts that are used in our Community Directory.

### Export

Contacts

1. Visit CiviCRM -> Search - Find Contacts
2. Set the search criteria to "is Organization"
   - this is because we only want organizations for our community directory
3. Click "search"
4. Click "Actions" -> "Export Contacts
5. Click "Select fields for export"
6. Choose "Organization - primary fields"
7. Click "Continue"
8. Click "Download File"

Relationships

1. Visit the CiviCRM [Relationships Report](https://westernfriend.org/civicrm/report/instance/5)
2. Click "Actions" -> "Download CSV"
3. Name the file "CiviCRM_relationships.csv"

### Import
