# Deployment

This work-in-progress document outlines steps necessary to deploy the site.

## DigitalOcean App Platform

We are using DigitalOcean App Platform to auto-deploy and manage the site.

## Environment variables

Environment variables are added through the DigitalOcean App Platform configuration for the specific app.

## Running migrate and collectstatic

The app can be configured with custom run command such as the following.

```sh
python manage.py migrate && python manage.py collectstatic --no-input
```
