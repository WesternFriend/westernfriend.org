# Contributing

There are many ways to contribute to this project, such as the following:

- Design
- Testing
- Ideas
- Accessibility
- Writing code

Feel free to stop by our [discussion area](https://github.com/WesternFriend/WF-website/discussions) to get involved with this project.

## Development

The following sections will guide you through a minimal development setup.

### Prerequisites

This project is built with [Python](https://www.python.org/), [Django](https://www.djangoproject.com/), and [Wagtail CMS](https://wagtail.io/).

Please make sure you have at least Python 3.10 installed. If you are developing on Windows, make sure to use PowerShell.

⚠️ Some Python installations provide only the `python3` command instead of `python`. If you get errors that the `python` command cannot be found, try running the same command using `python3`. This is an unfortunate consequence of the transition from Python 2 to 3.

### Setup

We have provided a Python script, `develop.py`, to automate several common tasks in your development workflow.

To see all available commands, you can use:

```sh
python develop.py -h
```

Here's a brief overview of what you can do:

- `python develop.py update-deps`: Update dependencies and check for issues.
- `python develop.py compile-deps`: Compile the project's dependencies.

⚠️ Note that some Python installations provide only the python3 command instead of python. If you get errors that the python command cannot be found, try running the same command using python3.

### Install

You can set up a development environment with the following steps. **Note:** some Python installations provide a `python` command instead of `python3`, so you may need to substitute `python` in the instructions below.

1. clone this repository
   - `git clone git@github.com:WesternFriend/WF-website.git`
2. Change into the application directory
   - `cd WF-website/`
3. create a virtual environment (using `python` or `python3`)
   - `python3 -m venv .venv`
4. activate the virtual environment
   - **Mac/Linux**: `source .venv/bin/activate`
   - **Windows PowerShell**: `.venv\Scripts\Activate.ps1`
5. install the project dependencies (using `pip` or `pip3`)
   - `pip install -r requirements.txt -r requirements-dev.txt`
6. activate `pre-commit` for automatic code maintenance
   - `pre-commit install`

### Running the background services

This project uses Docker to run a Postgres database, so we don't need to install Postgres locally. Start the development database and management UI.

```sh
docker compose up --detach
```

#### pgAdmin database access

We include pgAdmin in our Docker compose setup, which can be useful for exploring the database. the pgAdmin service should be running on localhost:5050 with the username and password being defined in the `docker-compose.yaml` file.

### Database migrations

Run database migrations to update the database structure to the latest changes. Use `python` or `python3`, depending on your system.

```sh
python manage.py migrate
```

### Create a superuser

Create a superuser that will be used to manage website content.

```sh
python manage.py createsuperuser
```

### Run the server

Run the local server, using `python` or `python3` command depending on your system.

Note: make sure to set the `DJANGO_DEBUG` environment variable to `true`, as follows.

```sh
DJANGO_DEBUG=true python manage.py runserver
```

Once the server is running, you can access it from http://localhost:8000

### Manage content

From there, you can begin adding the basic content. For convenience, there is a script to scaffold the initial content.

```sh
python manage.py scaffold_initial_content
```

or

```sh
python3 manage.py scaffold_initial_content
```

## Dependency management

We primarily use `pip` and `pip-tools` for project dependency management. To make things easier, we provide a helper script with several command aliases for common tasks, such as those below.

###Generating requirements files

```sh
python develop.py compile-deps
```

### Updating

```sh
python develop.py update-deps
```

### Adding and removing packages

To add or remove dependencies, simply add them to the dependencies list in pyproject.toml. Then, run the command from the "Generating requirements files" section above.

## Get help

If you have any difficulty or questions, please [open a support ticket](https://github.com/WesternFriend/WF-website/issues).

## Docker UI alternative

If you would like to use an alternative to Docker/Docker UI, try running [Colima](https://github.com/abiosoft/colima). Once Colima is installed, run the following command before running `docker compose up --detach`.

```sh
colima start
```

If Colima fails to start with an error about `ha.sock`, run the following command before running `colima start`

```sh
limactl stop -f colima
```

## Dependency management

### Generating requirements files

```sh
make compile-deps
```

### Updating

```sh
make update-deps
```

### Adding and removing packages

To add or remove dependencies, simply add them to the `dependencies` list in `pyproject.toml`.
