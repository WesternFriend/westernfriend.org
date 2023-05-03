# Contributing

There are many ways to contribute to this project, such as the following.

- design
- testing
- ideas
- accessibility
- writing code

Feel free to stop by our [discussion area](https://github.com/WesternFriend/WF-website/discussions) to get involved with this project.

## Development

The following sections will guide you through a minimal development setup.

### Prerequisites

This project is built with [Python](https://www.python.org/), [Django](https://www.djangoproject.com/), and [Wagtail CMS](https://wagtail.io/). We now use [Poetry](https://python-poetry.org/) for dependency / virtual environment management.

### Install

After [installing Poetry](https://python-poetry.org/docs/#installation), you can set up a development environment with the following steps:

1. clone this repository
   - `git clone git@github.com:WesternFriend/WF-website.git`
2. Change into the application directory
   - `cd WF-website/app/`
3. activate a Poetry virtual environment
   - `poetry shell`
4. install the project dependencies
   - `poetry install`
5. activate `pre-commit` for automatic code maintenance
   - `pre-commit install`

### Running the background services

Start the development database and management UI.

```sh
docker compose up --detach
```

#### pgAdmin database access

We include pgAdmin in our Docker compose setup, which can be useful for exploring the database. the pgAdmin service should be running on localhost:5050 with the username and password being defined in the `docker-compose.yaml` file.

### Database migrations

Run database migrations to update the database structure to the latest changes.

```sh
python manage.py migrate
```

 ### Create a superuser

Create a superuser that will be used to manage website content.
```sh
python manage.py createsuperuser
```

### Run the server

Run the local server

```sh
python manage.py runserver
```

Once the server is running, you can access it from http://localhost:8000

### Manage content

From there, you can begin adding the basic content. For convenience, there is a script to scaffold the initial content.

```sh
python manage.py scaffold_initial_content
```

## Get help

If you have any difficulty or questions, please [open a support ticket](https://github.com/WesternFriend/WF-website/issues).

## Docker UI alternative

If you would like to use an alternative to Docker/Docker UI, try running [Colima](https://github.com/abiosoft/colima). Once Colima is installed, run the following command before running `docker compose up --detach`.

```sh
colima start
```
