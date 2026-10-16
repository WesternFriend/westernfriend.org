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
  - [Set up the pre-deploy job on an existing app](#set-up-the-pre-deploy-job-on-an-existing-app)
  - [Enable the shared cache on an existing app](#enable-the-shared-cache-on-an-existing-app)
  - [Build the CSS during the deploy on an existing app](#build-the-css-during-the-deploy-on-an-existing-app)

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
   - Repository: WesternFriend/westernfriend.org
   - Branch: main
   - Source directory: /
   - Auto deploy: true
2. Under Resources
   - make sure there is a wf-website Web Service
     1. Python Buildpack,
     2. Procfile Buildpack,
     3. Custom Build Command
   - set the build command to `python manage.py tailwind build && python manage.py collectstatic --noinput`. The app-level `DISABLE_COLLECTSTATIC` variable (step 5) stops the buildpack from running `collectstatic` before the CSS exists. See [Build the CSS during the deploy on an existing app](#build-the-css-during-the-deploy-on-an-existing-app)
   - run command should be auto-configured as follows
     - `gunicorn core.wsgi --log-file -`
   - make sure there is a `migrate` Job that runs before every deploy, with the run command `python manage.py migrate && python manage.py createcachetable django_cache`. It runs once per deploy, before the web service starts, so web instances never race each other to migrate. See [Set up the pre-deploy job on an existing app](#set-up-the-pre-deploy-job-on-an-existing-app)
3. Edit the plan
   - select Basic during staging
   - select Pro (1 container) when deploying the preview/production site
4. Click Add Resource
   - add a dev database during staging (named `wf-staging-db`)
   - add a prod database when deploying the production site (named `wf-prod-db`)
5. Configure the environment variables. `.do/deploy.template.yaml` is the reference for every key, its scope, and placeholder value. Variables that both `wf-website` and the `migrate` job read are set once at the app level (**Settings** → **App-Level Environment Variables**), so the two can't drift apart. Variables only the web service reads are set on the `wf-website` component. A component-level variable overrides an app-level one with the same key. Mark keys, secrets, and passwords **Encrypt**.

   App level:

   - `DISABLE_COLLECTSTATIC` - `1` (scope: build time). The buildpack would otherwise run `collectstatic` before the build command compiles the CSS; `wf-website` runs it at the end of its build command instead, and the `migrate` job doesn't need it
   - `DATABASE_URL` - `${<database-name>.DATABASE_URL}` (scope: run time), the reference rather than the expanded connection string
   - `DJANGO_SECRET_KEY` - [random generated key](https://stackoverflow.com/a/67423892)
   - `DJANGO_DEBUG` - "True" or "False", should be "False" for production
   - `DJANGO_USE_SPACES` - "True" or "False", whether to use DO Spaces for static and media files. In this case, use "True"
   - `AWS_ACCESS_KEY_ID` - See:[Creating an Access Key](https://www.digitalocean.com/community/tutorials/how-to-create-a-digitalocean-space-and-api-key)
   - `AWS_SECRET_ACCESS_KEY` - See:[Creating an Access Key](https://www.digitalocean.com/community/tutorials/how-to-create-a-digitalocean-space-and-api-key)
   - `AWS_S3_REGION_NAME` - use the region name selected when setting up the DO Spaces Storage Bucket
   - `AWS_STORAGE_BUCKET_NAME` - the name of the DO Storage Bucket for static files
   - `DJANGO_DATABASE_CACHE` - "True" or "False" (default: False), whether to use the database cache shared by all workers instead of a per-process in-memory cache. See [Enable the shared cache on an existing app](#enable-the-shared-cache-on-an-existing-app)
   - `SENTRY_DSN` - used for error logging and analysis

   Every app-level variable except `DISABLE_COLLECTSTATIC` has the scope run time.

   On the `wf-website` component, scope run and build time:

   - `DJANGO_USE_SPACES` and the four `AWS_*` variables again, with the same values as at the app level. The build command's `collectstatic` uploads to Spaces only when `DJANGO_USE_SPACES` is "True" during the build, so `wf-website` needs them at build time. Giving them build-time scope here, rather than at the app level, keeps the Spaces credentials out of the `migrate` job's build, which installs dependencies and has no use for them. Use run and build time, not build time alone: a component-level variable replaces the app-level one with the same key. When you rotate the Spaces keys, update them in both places.

   On the `wf-website` component, scope run time:

   - `DJANGO_ALLOWED_HOSTS` - each allowed host needs only the domain (and subdomain if relevant), no protocol
   - `DJANGO_CSRF_TRUSTED_ORIGINS`- each origin should begin with a protocol, e.g., `https://...`
   - `PAYPAL_CLIENT_ENVIRONMENT` - one of "PRODUCTION" or "SANDBOX"
   - `PAYPAL_CLIENT_ID` - ID obtained from PayPal developer dashboard
   - `PAYPAL_CLIENT_SECRET` - client secret obtained from PayPal developer dashboard
   - `EMAIL_HOST` - SMTP host
   - `EMAIL_PORT` - SMTP port (default: 587)
   - `EMAIL_HOST_USER` - username for SMTP host
   - `EMAIL_HOST_PASSWORD` - password for SMTP user
   - `EMAIL_USE_TLS` - use Transport Layer Security (default: True)
   - `EMAIL_USE_SSL` - use implicit SSL instead of TLS (default: False). When set to True, also set `EMAIL_USE_TLS=False`: Django refuses to send email with both enabled, and TLS is on by default
   - `DEFAULT_FROM_EMAIL` - from address when sending mail (default: tech@westernfriend.org)
   - `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ZONE_ID` - let Wagtail purge published and unpublished pages from Cloudflare's cache. See [edge caching](specifications/edge_caching.md)
   - `DJANGO_PUBLIC_CACHE_EDGE_TTL` - seconds Cloudflare keeps a public page (default: 0, which marks every response private). See [edge caching](specifications/edge_caching.md)

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

## Set up the pre-deploy job on an existing app

Migrations and the cache table are created by a `migrate` job that App Platform runs once, before every deploy, rather than by the web service's run command. If each web instance ran `migrate` as it started, two instances starting together could race, and the one that lost would hit a database error and never start gunicorn. If the job fails, the deploy stops and the running version stays live.

Changing `.do/deploy.template.yaml` does not update a running app, because App Platform keeps its own copy of the app spec. Make these changes in the DigitalOcean dashboard. Move the shared variables to the app level first, add the job second, and shorten the web run command last, so every deploy along the way still runs migrations.

1. Note the `wf-website` component's current run command (in its component settings), so you can roll back.
2. Give the job its environment by moving the variables it shares with `wf-website` to the app level, rather than copying them onto the job: `DATABASE_URL`, `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_USE_SPACES`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_S3_REGION_NAME`, `AWS_STORAGE_BUCKET_NAME`, `DJANGO_DATABASE_CACHE`, `SENTRY_DSN`, and `DISABLE_COLLECTSTATIC`. See step 5 of [App](#app) for each one's scope.
   1. Go to the [Apps page](https://cloud.digitalocean.com/apps), select the app, open **Settings**, and add each variable under **App-Level Environment Variables** with the same value as on `wf-website`. For `DATABASE_URL`, use the same `${<database-name>.DATABASE_URL}` reference as `wf-website`, not the expanded connection string. Mark the keys and secrets **Encrypt**.
   2. Save and let the deploy finish. The running site doesn't change yet, because `wf-website`'s own copies override the app-level ones.
   3. Delete those variables from the `wf-website` component, except `DJANGO_USE_SPACES` and the four `AWS_*` variables. Keep those on `wf-website` and set their scope to **Run and build time**, so its build can upload static files to Spaces while the `migrate` job's build never sees the credentials. Save. After that deploy finishes, load the home page and check Sentry for new errors.
3. Add the `migrate` job, either by editing the app spec or through the **Add components** form. Editing the spec is more reliable; the form has failed to create the job.
   - **Edit the app spec:** in the app's **Settings**, find **App Spec** and click **Edit**. Add this under `spec:` (or add the entry to an existing `jobs:` list), then save. Leave the rest of the spec as it is, including any encrypted values shown as `EV[...]`.

     ```yaml
     jobs:
       - environment_slug: python
         github:
           branch: main
           deploy_on_push: true
           repo: WesternFriend/westernfriend.org
         instance_count: 1
         instance_size_slug: professional-xs
         kind: PRE_DEPLOY
         name: migrate
         run_command: python manage.py migrate && python manage.py createcachetable django_cache
         source_dir: /
     ```

   - **Add components:** click **Add components**, then choose **Create resources from source code**. Select the same source as `wf-website`: the WesternFriend/westernfriend.org GitHub repository, branch `main`, source directory `/`, with **Autodeploy** checked. Click **Next**. In the **Resource settings** table, under **Info**, click **Edit**, set **Resource type** to **Job**, and name it `migrate`. Under **Deployment settings**, set the run command to `python manage.py migrate && python manage.py createcachetable django_cache`. Under **Job trigger**, click **Edit** and select **Before every deploy**. The job gets its environment from the app-level variables, so add none to it. Click **Add resources**.

   The app redeploys; the `migrate` job runs first, then `wf-website`. The web run command still migrates too, which is harmless because both commands do nothing when there is nothing to do.
4. When the deploy finishes, open the deploy's logs and confirm the `migrate` job ran and printed its migration output without errors.
5. In the `wf-website` component settings, set the run command to `gunicorn core.wsgi --log-file -` and save. After that deploy finishes, load the home page and check Sentry for new errors.

The job runs while the previous version is still serving traffic, so a migration must not break the code that is already live (for example, drop a column only after a deploy that stops using it).

**Rolling back:** set the `wf-website` run command back to the one you noted in step 1, then delete the `migrate` component. The app-level variables can stay; `wf-website` reads them the same way it read its own copies.

## Enable the shared cache on an existing app

By default each gunicorn worker keeps its own in-memory cache, which is lost on every restart. Setting `DJANGO_DATABASE_CACHE=True` switches the site to Django's `DatabaseCache`, stored in the `django_cache` table, which all workers share and which survives deploys. Features that must agree across workers, such as rate limiting and cached PayPal subscription status, need it.

Changing `.do/deploy.template.yaml` does not update a running app, because App Platform keeps its own copy of the app spec. Make these changes in the DigitalOcean dashboard.

The cache table must exist before the switch is turned on; otherwise every cache read raises a database error and pages can fail with a 500. The `migrate` pre-deploy job creates it on every deploy with `python manage.py createcachetable django_cache`, whether or not the switch is on, so the table is always ready. `createcachetable` does nothing if the table already exists.

1. [Set up the pre-deploy job](#set-up-the-pre-deploy-job-on-an-existing-app) if the app does not have it yet, and let a deploy with it finish. The site keeps using the in-memory cache; that deploy only creates the table.
2. Add the app-level environment variable `DJANGO_DATABASE_CACHE` with the value `True` (scope: run time) and save. If `wf-website` has its own `DJANGO_DATABASE_CACHE`, delete it or set it to `True` too, because a component-level variable overrides the app-level one.
3. After the deploy finishes, confirm in the app console:

   ```sh
   python manage.py shell -c "from django.core.cache import caches; c = caches['default']; c.set('cache-check', 'ok', 60); print(type(c).__name__, c.get('cache-check'))"
   ```

   It should print `DatabaseCache ok`. Then load a few pages (home, a magazine article, and the login page) and check Sentry for new errors.

**Rolling back:** remove `DJANGO_DATABASE_CACHE` or set it to `False`. The site goes back to the per-process in-memory cache. The `django_cache` table can stay; nothing reads it.

**Scaling beyond one instance:** the table is created once per deploy by the `migrate` pre-deploy job, not as each web instance starts, so `wf-website` can run more than one instance without instances racing to create it.

## Build the CSS during the deploy on an existing app

The compiled Tailwind CSS (`theme/static/css/dist/styles.css`) is not committed. The `wf-website` build compiles it with `python manage.py tailwind build`, which downloads Tailwind's standalone binary, so the build needs no Node. The Python buildpack runs `collectstatic` on its own, but that happens before the custom build command, so before the CSS exists. Turning it off with `DISABLE_COLLECTSTATIC` and running `collectstatic` at the end of the build command puts the CSS in the static files.

Changing `.do/deploy.template.yaml` does not update a running app, because App Platform keeps its own copy of the app spec. Make these changes in the DigitalOcean dashboard, then deploy the commit that switches to the standalone binary (the one that stops committing the CSS). Do it in that order: a deploy of that commit without the new build command serves the site without its stylesheet.

1. Note the `wf-website` component's current build command (in its component settings), so you can roll back.
2. In the `wf-website` component settings, set the build command to `python manage.py tailwind build && python manage.py collectstatic --noinput`.
3. Add the app-level environment variable `DISABLE_COLLECTSTATIC` with the value `1` (scope: build time) and save. At the app level it also covers the `migrate` job, which serves no static files, so its build doesn't need `collectstatic`.
4. Make sure the `wf-website` component has its own `DJANGO_USE_SPACES` and four `AWS_*` variables with the scope **Run and build time**, not just run time. `collectstatic` now runs during the build, and it uploads to Spaces only if `DJANGO_USE_SPACES` is "True" then. Otherwise it writes the files to the build's local disk, which the running site never serves. Keep the app-level copies at run time only, so the `migrate` job's build doesn't get the credentials.
5. Saving these settings starts a rebuild of the code that is currently deployed. **That build is expected to fail** until the commit that switches to the standalone binary is deployed: older code still runs `tailwind build` through npm, so it stops with django-tailwind's "node.js and/or npm is not installed" error. App Platform keeps the last good deploy live when a build fails, so the site is unaffected.
6. Merge (or deploy) the commit that switches to the standalone binary. Its build runs the new build command and succeeds.
7. When that deploy finishes, open the `wf-website` build logs and confirm `tailwind build` printed `Done`. Then check where `collectstatic` put the files, from the line it prints last:
   - Uploaded to Spaces: no destination path, for example `3 static files copied, 1203 unmodified.` Files that haven't changed since the last upload are counted as unmodified.
   - Written to local disk instead: the line ends with a path, `... static files copied to '/workspace/static_root'.` The Spaces variables were not available at build time; recheck their scope (step 4) and redeploy.

   Then load the home page and check that it is styled, and that the stylesheet's URL points at the Spaces bucket.

**Rolling back:** set the build command back to the one you noted in step 1 and remove `DISABLE_COLLECTSTATIC`. Without a committed CSS file, the site then has no stylesheet, so also revert the commit that stopped committing it.
