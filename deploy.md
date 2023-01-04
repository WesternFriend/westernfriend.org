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

### Data prep

## Environment variables

Environment variables are added through the DigitalOcean App Platform configuration for the specific app.

## Running migrate and collectstatic

The app can be configured with custom run command such as the following.

```sh
python manage.py migrate && python manage.py collectstatic --no-input
```
