# Deployment

This work-in-progress document outlines the steps necessary to deploy the site.

- [Deployment](#deployment)
  - [Static Files](#static-files)
  - [App](#app)
    - [Example Configuration](#example-configuration)
  - [Domain](#domain)
  - [Initialize the App](#initialize-the-app)
  - [Scaffold Initial Content](#scaffold-initial-content)
  - [Data prep/import](#data-prepimport)

## Static Files

Before creating the app, we need a space to store static files. For that, we will use DO Spaces.

1. Create a [Spaces Object Storage Bucket](https://cloud.digitalocean.com/spaces)
2. Edit the [Spaces CORS settings](https://docs.digitalocean.com/products/spaces/how-to/configure-cors/) with the following values
3. [Create an Access Key](https://docs.digitalocean.com/products/spaces/how-to/manage-access/#access-keys) - save these values as they are used later

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

1. Create a new App with the following settings
   - Create Resource from Source Code: GitHub
   - Repository: WesternFriend/WF-website
   - Branch: main
   - Source directory: /
   - Auto deploy: true
2. Under Resources
   - make sure there is a wf-website Web Service
     1. Python Buildpack,
     2. Procfile Buildpack,
     3. Custom Build Command
   - run command should be auto-configured as follows
     - `python manage.py migrate && gunicorn core.wsgi --log-file -`
3. Edit the plan
   - select Basic during staging
   - select Pro (1 container) when deploying the preview/production site
4. Click Add Resource
   - add a dev database during staging (named `wf-staging-db`)
   - add a prod database when deploying the production site (named `wf-prod-db`)
5. Configure all necessary [environment variables](#environment-variables) at the component level (`wf-website`), not the app, which combines the `wf-website` and `db` components

   - `DJANGO_CORS_ALLOWED_ORIGINS` - each origin should begin with a protocol, e.g., `https://...`
   - `DJANGO_ALLOWED_HOSTS` - each allowed host needs only the domain (and subdomain if relevant), no protocol
   - `DJANGO_CSRF_TRUSTED_ORIGINS`- each origin should begin with a protocol, e.g., `https://...`
   - `DJANGO_SECRET_KEY` - [random generated key](https://stackoverflow.com/a/67423892)
   - `DJANGO_DEBUG` - "True" or "False", should be "False" for production
   - `DJANGO_USE_SPACES` - "True" or "False", whether to use DO Spaces for static files. In this case, use "True".
   - `AWS_ACCESS_KEY_ID` - See:[Creating an Access Key](https://www.digitalocean.com/community/tutorials/how-to-create-a-digitalocean-space-and-api-key)
   - `AWS_SECRET_ACCESS_KEY` - See:[Creating an Access Key](https://www.digitalocean.com/community/tutorials/how-to-create-a-digitalocean-space-and-api-key)
   - `AWS_S3_REGION_NAME` - use the region name selected when setting up the DO Spaces Storage Bucket
   - `AWS_STORAGE_BUCKET_NAME` - the name of the DO Storage Bucket for static files
   - `PAYPAL_CLIENT_ENVIRONMENT` - one of "PRODUCTION" or "SANDBOX"
   - `PAYPAL_CLIENT_ID` - ID obtained from PayPal developer dashboard
   - `PAYPAL_CLIENT_SECRET` - client secret obtained from PayPal developer dashboard
   - `SENTRY_DSN` - used for error logging and analysis
   - `RECAPTCHA_PUBLIC_KEY` - a.k.a. site key on reCAPTCHA settings
   - `RECAPTCHA_PRIVATE_KEY` - a.k.a. secret key on reCAPTCHA settings
   - `EMAIL_HOST` - SMTP host
   - `EMAIL_PORT` - SMTP port (default: 587)
   - `EMAIL_HOST_USER` - username for SMTP host
   - `EMAIL_HOST_PASSWORD` - password for SMTP user
   - `EMAIL_USE_TLS` - use Transport Layer Security (default: True)
   - `DEFAULT_FROM_EMAIL` - from address when sending mail (default: tech@westernfriend.org)

6. Edit the App Info with the following settings
   1. Give the app a meaningful name
   2. Set the Region to San Francisco, so it is closer to most WesternFriend community

## Domain

After the initial app is deployed, configure a domain (or subdomain) on our registrar that points to the deployed app via a CNAME record.

Add a domain name [under the app settings](https://docs.digitalocean.com/products/app-platform/how-to/manage-domains). Be sure to add a corresponding CNAME record to the domain DNS configuration. DNS settings are managed wherever the domain is registered.

## Initialize the App

Access the app console via DigitalOcean admin UI, and run the following commands to initialize the app.

1. Run migrations
   - `python manage.py migrate`
2. Create a superuser
   - `python manage.py createsuperuser`
3. Collect static files
   - `python manage.py collectstatic --no-input`

**NOTE:** At this point, make sure to check the DigitalOcean Space where static files should be stored, to ensure the app has access to the storage space. If the staticfiles are not uploaded to the storage space, check the Spaces and App configurations and try again before proceeding with further steps.

## Scaffold Initial Content

We have a pre-defined content tree for the primary website structure. To save some time, run the following command in the DO App console to scaffold the initial content tree.

```py
python manage.py scaffold_initial_content
```

## Data prep/import

Refer to the [content migration](CONTENT_MIGRATION.md) guide for further details about preparing data for import. Once the data have been prepared, use the following steps to import them to the online website.

1. copy all import files (CSV format) to the DO Spaces bucket for import data
2. run the import commands below via the DO App console, using the bucket location (HTTPS) as a target
   - of particular importance, make sure to open and re-save the CiviCRM CSV files using LibreOffice since they cause errors when exported directly from CiviCRM

First, download all migration data.

```sh
python manage.py download_migration_data <https://bucket-location.url>
```

Then, run all importers with a single command. Note: this may take 30-60 minutes.

```sh
python manage.py import_all_content
```
