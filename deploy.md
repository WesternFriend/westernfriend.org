# Deployment

This work-in-progress document outlines steps necessary to deploy the site.

## DigitalOcean App Platform

We are using DigitalOcean App Platform to auto-deploy and manage the site.

1. create a new DigitalOcean App, such as "westernfriend-website"
2. make sure to add a database along with the app during the creation process or after
3. configure the deployment to be triggered when changes are merged to the `main` branch of this repo
4. configure a domain (or subdomain) to point to the deployed app

### After the initial deployment

1. run migrations
2. create a superuser

### Static files

We need a space to store static files. For that, we will use DO Spaces.

1. create a Spaces Bucket
2. edit the CORS settings with the following values (substituting actual values where needed)

```yaml
Origin: https://domain-name.com
Allowed Methods: GET
Allowed Headers:
- Access-Control-Allow-Origin
- Referer
Access Control Max Age: 600
```

## Environment variables

Environment variables are added through the DigitalOcean App Platform configuration for the specific app. Make sure to define the following environment variables with corresponding values.

- `DJANGO_CORS_ALLOWED_ORIGINS` - each origin should begin with a protocol, e.g., `https://`
- `DJANGO_ALLOWED_HOSTS` - each allowed host needs only the domain (and subdomain if relevant), no protocol
- `DJANGO_CSRF_TRUSTED_ORIGINS`- each origin should begin with a protocol, e.g., `https://`
- `DJANGO_SECRET_KEY` - [random generated key](https://stackoverflow.com/a/67423892)
- `DEBUG` - "True" or "False", should be "False" for production
- `USE_SPACES` - "True" or "False", whether to use DO Spaces for static files. In this case, use "True".
- `AWS_S3_REGION_NAME` - use the region name selected when setting up the DO Spaces Storage Bucket

## Running migrate and collectstatic

The app can be configured with custom run command such as the following.

```sh
python manage.py migrate && python manage.py collectstatic --no-input
```

### Scaffold initial content

We have a pre-defined content tree for the primary website structure. In order to save some time, run the following command in the DO App console to scaffold the initial content tree.

```py
python manage.py scaffold_initial_content
```

### Data prep/import

Refer to the [content migration](CONTENT_MIGRATION.md) guide for further details about preparing data for import. Once the data have been prepared, use the following steps to import them to the online website.

1. copy all import files (CSV format) to the DO Spaces bucket for import data
2. run the import commands via the DO App console, using the bucket location (HTTPS) as a target


