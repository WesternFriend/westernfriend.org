# Contributing Guide

## Introduction

Whether you're an experienced developer or this is your first open source contribution, we welcome your support! You can contribute to WesternFriend's project in various ways:

- **Design**
- **Testing**
- **Ideas**
- **Accessibility**
- **Writing code**

For general discussions and to get involved with the community, visit our [discussion area](https://github.com/WesternFriend/WF-website/discussions).

## Development Setup

Follow the steps below to set up your development environment.

### Prerequisites

- [Python 3.10](https://www.python.org/) or higher
- [UV](https://github.com/astral-sh/uv) - Modern Python package manager
- [Django](https://www.djangoproject.com/)
- [Wagtail CMS](https://wagtail.io/)

**Note:** If you're using Windows, please use PowerShell. If your system uses the `python3` command instead of `python`, substitute it as needed.

Optionally, install [Claude context mode](https://github.com/mksglu/claude-context-mode) manager for better AI-assisted development using Claude Code:

```bash
/plugin marketplace add mksglu/claude-context-mode
/plugin install context-mode@claude-context-mode
```

### Setup

1. **Clone the Repository**: `git clone git@github.com:WesternFriend/westernfriend.org.git`
2. **Change into the Application Directory**: `cd  westernfriend.org/`
3. **Create Virtual Environment and Install Dependencies**:

   ```sh
   uv sync
   ```

4. **Activate the Virtual Environment**:
   - **Mac/Linux**: `source .venv/bin/activate`
   - **Windows PowerShell**: `.venv\Scripts\Activate.ps1`
5. **Activate Pre-Commit**: `pre-commit install`. CI runs the same hooks on every pull request and comments with anything that needs fixing, so installing them locally catches problems before you push. Run `pre-commit run --all-files` to check everything at once.

### Running Background Services

This project uses Docker to manage a Postgres database.

- **Start the Database**: `docker compose up --detach`
- **pgAdmin Access**: Use localhost:5050 (credentials in the `docker-compose.yaml` file)

### Application Configuration

1. **Create .env File** (with `DJANGO_DEBUG=true`)
2. **Run Database Migrations**: `python manage.py migrate`
3. **Add Content**: `python manage.py seed_dev_content` (see [Development content](#development-content))
4. **Run the Server**: `python manage.py runserver` (access from http://localhost:8000)

### Development content

`python manage.py seed_dev_content` fills an empty database with a complete mock website, so you can try every page, run UX and accessibility audits, and test the admin without a copy of production data. It scaffolds the site structure, then adds:

- people, organizations, and meetings nested yearly > quarterly > monthly > worship group, with addresses, worship times, and clerks
- magazine issues with articles, departments, authors, and tags; the newest issues fall inside the subscriber-only window and the rest are public
- deep archive issues, library items with facets and topics, events (upcoming, past, featured, and "other"), news, memorials, meeting and board documents, blog posts, and bookstore books and orders
- placeholder cover, product, and illustration images with alt text
- accounts for `admin@example.com` (superuser), `subscriber@example.com`, `expired-subscriber@example.com`, and `reader@example.com`, all with the password `westernfriend-dev`

The data is deliberately varied: very long titles, non-ASCII names, drafts, a sold-out book, a login-only page, and items with no authors or facets all appear somewhere.

| Option | Effect |
| --- | --- |
| `--scale small\|medium\|large` | How much content to create (default `medium`, about 1,000 pages). Use `large` to test pagination and performance. |
| `--seed N` | Random seed. The same seed builds the same site on the same day. |
| `--no-images` | Skip the generated images. |
| `--reset` | Delete the existing page tree, seed images, and dev accounts first. |

The command only runs with `DJANGO_DEBUG=true`, and never when Cloudflare cache purging is configured, so it can't touch a live site. It also refuses to run on a database that has any content beyond the scaffolded structure, unless you pass `--reset`.

Its tests seed a small site, then use it as a smoke test: every live page and every page type's admin form must render. They take under a minute and are tagged `seed`. `python manage.py test` includes them; add `--exclude-tag seed` for a faster run, or `--tag seed` to run only them. CI runs them in their own job, alongside the main tests.

The field values come from the factories in each app's `factories.py`, which tests use too; the seeder in `cli/dev_content/` decides how much content to create and how it connects. To seed a new model, give it a factory with Faker defaults (and traits for the variations worth showing), then add it to the seeder.

To edit the Tailwind CSS, run the following command in a separate terminal:

```bash
python manage.py tailwind start
```

### Dependency Management

We use UV for dependency management with dependencies defined in `pyproject.toml`. Use the following commands:

- **Install All Dependencies**: `uv sync`
- **Install with Dev Dependencies**: `uv sync --all-extras`
- **Update Dependencies**: `uv sync --upgrade`
- **Add New Packages**:
  - For regular dependencies: `uv add <package-name>`
  - For development dependencies: `uv add --dev <package-name>`
  - After adding packages, run `uv sync` to ensure your environment is up to date

## Alternatives

### Docker UI

If you prefer an alternative to Docker/Docker UI, try [Colima](https://github.com/abiosoft/colima).

- **Start Colima**: `colima start`
- If you face an error, use `limactl stop -f colima`, then re-run the start command.

## Support

Need help? Feel free to [open a support ticket](https://github.com/WesternFriend/WF-website/issues).

## Conclusion

We appreciate your interest and contribution to the WesternFriend project. Happy coding!
