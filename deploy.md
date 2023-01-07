# Deployment

This work-in-progress document outlines the steps necessary to deploy the site.

- [Deployment](#deployment)
  - [Static Files](#static-files)
  - [App](#app)
    - [Example Configuration](#example-configuration)
    - [Environment Variables](#environment-variables)
  - [Domain](#domain)
  - [Initialize the App](#initialize-the-app)
  - [Scaffold Initial Content](#scaffold-initial-content)
  - [Data prep/import](#data-prepimport)

## Static Files

Before creating the app, we need a space to store static files. For that, we will use DO Spaces.

1. Create a [Spaces Object Storage Bucket](https://cloud.digitalocean.com/spaces)
2. Edit the [Spaces CORS settings](https://docs.digitalocean.com/products/spaces/how-to/configure-cors/) with the following values

```yaml
Origin: https://<domain.TLD>
Allowed Methods: GET
Allowed Headers:
- Access-Control-Allow-Origin
- Referer
Access Control Max Age: 600
```

## App

We are using the DigitalOcean App Platform to auto-deploy and manage the site. 

Set up the site by following the steps below. The order of steps matters. So, be careful about jumping ahead before completing any given step.

1. Create a Storage Bucket for site static media and file uploads
2. Create a new App with the following considerations during the creation process
   1. Make sure to add a database
   2. Deployment is triggered when changes are merged to the `main` branch
   3. Configure all necessary [environment variables](#environment-variables) while creating the App
   4. Edit the App Info with the following settings
      1. Give the app a meaningful name
      2. Set the Region to San Francisco, so it is closer to most WesternFriend community
3. configure a domain (or subdomain) to point to the deployed app

### Example Configuration

Below is an example configuration for our staging setup.

```yaml
App
- wf-website-staging
   - wf-website: Web Service / Dockerfile
   - db: Dev Database

Environment Variables
- Global: 0 environment variables
   - wf-website: 9 environment variables

Info
   - Name: wf-website-staging
   - Region: San Francisco

Project: Western Friend
```

### Environment Variables

Environment variables are added through the DigitalOcean App Platform configuration for the specific app. Make sure to define the following environment variables with corresponding values. Also, make sure to quote all of the environment variable values, to avoid potential pitfalls or unexpected behavior.

- `DJANGO_CORS_ALLOWED_ORIGINS` - each origin should begin with a protocol, e.g., `"https://..."`
- `DJANGO_ALLOWED_HOSTS` - each allowed host needs only the domain (and subdomain if relevant), no protocol
- `DJANGO_CSRF_TRUSTED_ORIGINS`- each origin should begin with a protocol, e.g., `"https://..."`
- `DJANGO_SECRET_KEY` - [random generated key](https://stackoverflow.com/a/67423892)
- `DEBUG` - "True" or "False", should be "False" for production
- `USE_SPACES` - "True" or "False", whether to use DO Spaces for static files. In this case, use "True".
- `AWS_S3_REGION_NAME` - use the region name selected when setting up the DO Spaces Storage Bucket
- `AWS_STORAGE_BUCKET_NAME` - the name of the DO Storage Bucket for static files

## Domain

Add a domain name [under the app settings](https://docs.digitalocean.com/products/app-platform/how-to/manage-domains). Be sure to add a corresponding CNAME record to the domain DNS configuration. DNS settings are managed wherever the domain is registered.

## Initialize the App

Access the app console via DigitalOcean admin UI, and run the following commands to initialize the app.

1. Run migrations
    - `python manage.py migrate`
2. Create a superuser
   - `python manage.py createsuperuser`
3. Collect static files
   - `python manage.py collectstatic --no-input`

At this point, make sure to check the DigitalOcean Space where static files should be stored, to ensure the app has access to the storage space.

## Scaffold Initial Content

We have a pre-defined content tree for the primary website structure. To save some time, run the following command in the DO App console to scaffold the initial content tree.

```py
python manage.py scaffold_initial_content
```

## Data prep/import

Refer to the [content migration](CONTENT_MIGRATION.md) guide for further details about preparing data for import. Once the data have been prepared, use the following steps to import them to the online website.

1. copy all import files (CSV format) to the DO Spaces bucket for import data
2. run the import commands via the DO App console, using the bucket location (HTTPS) as a target
