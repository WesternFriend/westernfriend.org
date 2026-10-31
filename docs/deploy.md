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
  - [Serve the site over HTTPS behind the proxy](#serve-the-site-over-https-behind-the-proxy)

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
     1. Node.js Buildpack,
     2. Python Buildpack,
     3. Procfile Buildpack,
     4. Custom Build Command
   - set the build command to `npm ci --include=dev && npm run build:css && python manage.py collectstatic --noinput`. The app-level `DISABLE_COLLECTSTATIC` variable (step 5) stops the buildpack from running `collectstatic` before the CSS exists. See [Build the CSS during the deploy on an existing app](#build-the-css-during-the-deploy-on-an-existing-app)
   - run command should be auto-configured as follows
     - `gunicorn core.wsgi --log-file -`
   - make sure there is a `migrate` Job that runs before every deploy, with the run command `python manage.py migrate && python manage.py createcachetable django_cache`. It runs once per deploy, before the web service starts, so web instances never race each other to migrate. See [Set up the pre-deploy job on an existing app](#set-up-the-pre-deploy-job-on-an-existing-app)
3. Edit the plan
   - select Basic during staging
   - select Pro (1 container) when deploying the preview/production site
4. Click Add Resource
   - add a dev database during staging (named `wf-staging-db`)
   - add a prod database when deploying the production site (named `wf-prod-db`)
5. Configure the environment variables. `.do/deploy.template.yaml` is the reference for every required key, its scope, and placeholder value. Variables that both `wf-website` and the `migrate` job read are set once at the app level (**Settings** → **App-Level Environment Variables**), so the two can't drift apart. Variables only the web service reads are set on the `wf-website` component. A component-level variable overrides an app-level one with the same key. Mark keys, secrets, and passwords **Encrypt**.

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

   Every app-level variable except `DISABLE_COLLECTSTATIC` has the scope run time.

   On the `wf-website` component, scope run and build time:

   - `DJANGO_USE_SPACES` and the four `AWS_*` variables again, with the same values as at the app level. The build command's `collectstatic` uploads to Spaces only when `DJANGO_USE_SPACES` is "True" during the build, so `wf-website` needs them at build time. Giving them build-time scope here, rather than at the app level, keeps the Spaces credentials out of the `migrate` job's build, which installs dependencies and has no use for them. Use run and build time, not build time alone: a component-level variable replaces the app-level one with the same key. When you rotate the Spaces keys, update them in both places.

   On the `wf-website` component, scope run time:

   - `DJANGO_ALLOWED_HOSTS` - each allowed host needs only the domain (and subdomain if relevant), no protocol
   - `DJANGO_CANONICAL_HOST` - destination hostname without a protocol, for example `westernfriend.org`; defaults to empty
   - `DJANGO_REDIRECT_HOSTS` - comma-separated hostnames to redirect to the canonical host over HTTPS, without protocols or ports; defaults to empty. For production, use `coral-app-qpf8k.ondigitalocean.app`. Keep `DJANGO_ALLOWED_HOSTS` restricted to the hosts Django should serve
   - `DJANGO_CSRF_TRUSTED_ORIGINS`- each origin should begin with a protocol, e.g., `https://...`
   - `PAYPAL_CLIENT_ENVIRONMENT` - one of "PRODUCTION" or "SANDBOX"
   - `PAYPAL_CLIENT_ID` - ID obtained from PayPal developer dashboard
   - `PAYPAL_CLIENT_SECRET` - client secret obtained from PayPal developer dashboard
   - `DJANGO_PUBLIC_CACHE_EDGE_TTL` - seconds Cloudflare keeps a public page (default: 0, which marks every response private). See [edge caching](specifications/edge_caching.md)

   Optional features. These are not in the template, because each feature turns on as soon as its variables are set, and a placeholder value breaks it. Add them in the dashboard only once you have real values.

   - `SENTRY_DSN` - app level, scope run time. Turns on error reporting to Sentry, for both `wf-website` and the `migrate` job. A value that isn't a valid DSN stops the app from starting
   - `EMAIL_HOST`, `EMAIL_HOST_USER`, and `EMAIL_HOST_PASSWORD` - `wf-website`, scope run time. When all three are set, the site sends email over SMTP with them; until then it only prints email to the log. Placeholder values make every email (account activation, password reset) fail
     - `EMAIL_PORT` - SMTP port (default: 587)
     - `EMAIL_USE_TLS` - use Transport Layer Security (default: True)
     - `EMAIL_USE_SSL` - use implicit SSL instead of TLS (default: False). When set to True, also set `EMAIL_USE_TLS=False`: Django refuses to send email with both enabled, and TLS is on by default
     - `DEFAULT_FROM_EMAIL` - from address when sending mail (default: tech@westernfriend.org)
   - `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ZONE_ID` - `wf-website`, scope run time. When both are set, Wagtail purges published and unpublished pages from Cloudflare's cache. Placeholder values make every purge fail, so Cloudflare keeps serving stale pages. See [edge caching](specifications/edge_caching.md)

   HTTPS overrides. Leave these unset: with `DJANGO_DEBUG` "False", the site already redirects to HTTPS and sends HSTS without them. They exist so the rollout can be adjusted without a code change. See [Serve the site over HTTPS behind the proxy](#serve-the-site-over-https-behind-the-proxy)

   - `DJANGO_SECURE_SSL_REDIRECT` - `wf-website`, scope run time (default: "true"). Any value other than "true" or "1" turns off the redirect from HTTP to HTTPS
   - `DJANGO_SECURE_HSTS_SECONDS` - `wf-website`, scope run time (default: 3600, one hour). The `max-age` of the `Strict-Transport-Security` header. `0` stops sending the header

6. Edit the App Info with the following settings
   1. Give the app a meaningful name
   2. Set the Region to San Francisco, so it is closer to most WesternFriend community

## Domain

After the initial app is deployed, configure a domain (or subdomain) on our registrar that points to the deployed app via a CNAME record.

Add a domain name [under the app settings](https://docs.digitalocean.com/products/app-platform/how-to/manage-domains). Be sure to add a corresponding CNAME record to the domain DNS configuration. DNS settings are managed wherever the domain is registered.

For the existing production app, deploy the redirect middleware and set the web service (`westernfriend-website`) runtime variables `DJANGO_CANONICAL_HOST=westernfriend.org` and `DJANGO_REDIRECT_HOSTS=coral-app-qpf8k.ondigitalocean.app` in App Platform. The template calls its web service `wf-website`; the existing production service has a different name. The template does not update an existing app. Verify that the default domain returns a 301 to the same path and query on `https://westernfriend.org`, and that an unlisted host still receives a 400.

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
2. Give the job its environment by moving the variables it shares with `wf-website` to the app level, rather than copying them onto the job: `DATABASE_URL`, `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_USE_SPACES`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_S3_REGION_NAME`, `AWS_STORAGE_BUCKET_NAME`, `DJANGO_DATABASE_CACHE`, `DISABLE_COLLECTSTATIC`, and `SENTRY_DSN` if the app uses Sentry. See step 5 of [App](#app) for each one's scope.
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

The compiled CSS is not committed. The web service needs both Node.js 24/npm 11 and Python during its build. The root `package.json` enables Node detection and declares its supported version; keep the Node.js buildpack before Python in the dashboard's buildpack order. Keep the web run command as `gunicorn core.wsgi --log-file -`.

The permanent build command is:

```sh
npm ci --include=dev && npm run build:css && python manage.py collectstatic --noinput
```

Keep the app-level `DISABLE_COLLECTSTATIC=1` at build time, so the Python buildpack does not collect files before the CSS exists. The web service's Spaces settings must have build-time scope as well as runtime scope, so `collectstatic` uploads the CSS to the same bucket the site serves from. The migration job does not need to compile CSS.

Changing `.do/deploy.template.yaml` does not update the live app spec. Before merging the npm migration, set this temporary web build command in the dashboard:

```sh
if [ -f package-lock.json ]; then
  npm ci --include=dev && npm run build:css || exit 1
else
  python manage.py tailwind build || exit 1
fi
python manage.py collectstatic --noinput
```

This builds the currently deployed standalone code as well as the npm migration. Saving the command redeploys the current code: confirm that deploy succeeds before merging. When the migration deploy builds, confirm that the logs show Node.js and Python buildpacks, the locked npm installation and CSS compilation, then `collectstatic`. If Node.js is not detected, configure the buildpack order in the dashboard before retrying; keep the last successful deployment live.

After the migration deploy succeeds, simplify the live command to the permanent command above. Check the site's stylesheet URL points at Spaces and that the library filters, checkout, and registration forms are styled in light and dark themes.

**Rolling back:** restore the previous code and temporary build command together. Keep `DISABLE_COLLECTSTATIC=1` and collect files after compiling CSS.

## Serve the site over HTTPS behind the proxy

TLS ends at App Platform's proxy, so the app itself receives plain HTTP. With `DJANGO_DEBUG` "False", Django trusts the proxy's `X-Forwarded-Proto: https` header to know a request was HTTPS, and then:

- redirects plain-HTTP requests to HTTPS (a permanent 301 redirect);
- marks the session and CSRF cookies `Secure`, so browsers send them only over HTTPS;
- builds the links in password-reset and account-activation emails with `https://`;
- sends `Strict-Transport-Security` with a one-hour `max-age`, without `includeSubDomains` or `preload`.

None of this needs a new variable; the defaults apply on the first deploy. With `DJANGO_DEBUG` "True" (local development), nothing changes.

Trusting the header is only safe if the proxy sets it itself and replaces any `X-Forwarded-Proto` a client sends. A DigitalOcean community answer says App Platform does both; its documentation doesn't say either way. If the site ever moves behind a proxy that passes the client's header through, make that proxy overwrite it. Don't remove `SECURE_PROXY_SSL_HEADER` from `core/settings.py` instead: every request would then look like plain HTTP, so while `DJANGO_SECURE_SSL_REDIRECT` is on, every page would redirect to itself. If the setting ever has to go, set `DJANGO_SECURE_SSL_REDIRECT` to "false" first, and expect `http://` links in emails and no HSTS header.

Before deploying, make sure `wf-website` has `DJANGO_ALLOWED_HOSTS` and `DJANGO_CSRF_TRUSTED_ORIGINS` set (step 5 of [App](#app)), with `https://` origins. Their defaults now list only `127.0.0.1` and `localhost`, so an app that relied on the default no longer accepts requests for its real domain.

If Cloudflare is in front of the app, its SSL/TLS encryption mode must be **Full** or **Full (strict)**, not **Flexible**. Flexible connects to the app over plain HTTP, so the header says `http` and every request redirects to itself.

1. Deploy the change. No dashboard settings change.
2. When the deploy finishes, check the redirect and the headers from a terminal:

   ```sh
   curl -sI http://<domain.TLD>/
   curl -sI https://<domain.TLD>/
   ```

   The first should answer `301 Moved Permanently` with `Location: https://<domain.TLD>/`. The second should answer `200` and include `Strict-Transport-Security: max-age=3600`.
3. Load the login page in a browser and check, in the developer tools, that the `csrftoken` cookie is marked `Secure`. Request a password reset and check that the link in the email starts with `https://`.
4. Once HTTPS is confirmed everywhere, raise `DJANGO_SECURE_HSTS_SECONDS` on `wf-website` (for example to `31536000`, one year). Raise it only when you're sure: a browser that received a long `max-age` keeps using HTTPS for that long unless it comes back and receives a shorter one, so visitors who don't return can't be released early.

If every page redirects to itself (the browser shows "too many redirects"), the proxy header isn't arriving. Set `DJANGO_SECURE_SSL_REDIRECT` to "false" on `wf-website` and save; the site then serves without the redirect while you find out why. The same applies to any HTTP health check that reaches the app without the header: it would get a redirect instead of a `200`.

**Rolling back:** set `DJANGO_SECURE_SSL_REDIRECT` to "false" to stop the redirect, and `DJANGO_SECURE_HSTS_SECONDS` to `0` to stop sending HSTS. With `0`, Django sends no header at all, so a browser that already saved HSTS keeps using HTTPS until the last `max-age` it received runs out, which is one hour with the default. To release returning visitors sooner, set it to `1` instead: Django then sends `max-age=1` over HTTPS, which replaces the saved value, so it lapses a second later. This only works while the proxy's `X-Forwarded-Proto: https` header is arriving: without it Django treats every request as plain HTTP and sends no HSTS header at all, so restore the header first. Visitors who don't come back keep their saved `max-age`.
