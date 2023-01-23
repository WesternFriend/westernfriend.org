# Importing data

This document outlines the steps involved in importing data.

## Download data

Download all data from the Drupal Website. Make sure all data are exported around the same day in order to ensure integrity.

## Scaffold initial content

We need a basic content structure in order to import the Drupal data. Scaffold the initial content with the following command.

```sh
python manage.py scaffold_initial_content
```

## Import Drupal content

The Drupal content model is organized into several sections, each outlined below.

### Magazine

The magazine content needs to be imported in a particular order.

Note: there is a single `import_magazine` command to import magazine data that assumes the files have specific names:

- departments.csv
- authors.csv
- issues.csv
- articles.csv

Otherwise, the data can be more manually imported by running the following commands.

1. departments
   - `python manage.py import_magazine_departments --file <file_path>`
2. authors
   - `python manage.py import_magazine_authors --file <file_path>`
3. issues
   - `python manage.py import_magazine_issues --file <file_path>`
4. articles
   `python manage.py import_magazine_articles --articles_file <file_path> --authors_file <file_path>`
