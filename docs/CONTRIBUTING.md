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
- [Django](https://www.djangoproject.com/)
- [Wagtail CMS](https://wagtail.io/)

**Note:** If you're using Windows, please use PowerShell. If your system uses the `python3` command instead of `python`, substitute it as needed.

### Setup

1. **Clone the Repository**: `git clone git@github.com:WesternFriend/WF-website.git`
2. **Change into the Application Directory**: `cd WF-website/`
3. **Create a Virtual Environment**: `python3 -m venv .venv`
4. **Activate the Virtual Environment**:
   - **Mac/Linux**: `source .venv/bin/activate`
   - **Windows PowerShell**: `.venv\Scripts\Activate.ps1`
5. **Install Project Dependencies**: `pip install -r requirements.txt -r requirements-dev.txt`
6. **Activate Pre-Commit**: `pre-commit install`

### Running Background Services

This project uses Docker to manage a Postgres database.

- **Start the Database**: `docker compose up --detach`
- **pgAdmin Access**: Use localhost:5050 (credentials in the `docker-compose.yaml` file)

### Application Configuration

1. **Run Database Migrations**: `python manage.py migrate`
2. **Create a Superuser**: `python manage.py createsuperuser`
3. **Create .env File** (with `DJANGO_DEBUG=true`)
4. **Run the Server**: `python manage.py runserver` (access from http://localhost:8000)
5. **Scaffold Initial Content**: `python manage.py scaffold_initial_content`

### Dependency Management

We use `pip` and `pip-tools`. Use the following commands to manage dependencies:

- **Generate Requirements Files**: `python develop.py compile-deps`
- **Update Dependencies**: `python develop.py update-deps`
- **Add/Remove Packages**: Modify the `dependencies` list in `pyproject.toml`, then recompile.

## Alternatives

### Docker UI

If you prefer an alternative to Docker/Docker UI, try [Colima](https://github.com/abiosoft/colima).

- **Start Colima**: `colima start`
- If you face an error, use `limactl stop -f colima`, then re-run the start command.

## Support

Need help? Feel free to [open a support ticket](https://github.com/WesternFriend/WF-website/issues).

## Conclusion

We appreciate your interest and contribution to the WesternFriend project. Happy coding!
