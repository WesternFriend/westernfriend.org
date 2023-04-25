# Contributing

There are many ways to contribute to this project, such as the following.

- design
- testing
- ideas
- accessibility
- writing code

Feel free to stop by our [discussion area](https://github.com/WesternFriend/WF-website/discussions) to get involved with this project.

## Development

This project is built with [Python](https://www.python.org/), [Django](https://www.djangoproject.com/), and [Wagtail CMS](https://wagtail.io/). We now use [Poetry](https://python-poetry.org/) for dependency / virtual environment management. After [installing Poetry](https://python-poetry.org/docs/#installation), you can set up a development environment with the following steps:

1. clone this repository
   - `git clone git@github.com:WesternFriend/WF-website.git`
2. Change into the application directory
   - `cd WF-website/app/`  
3. activate a Poetry virtual environment
   - `poetry shell`
4. install the project dependencies
   - `poetry install`
5. activate `autohooks` for automatic code maintenance
   - `poetry run autohooks activate --mode poetry`
6. start the development database
   - `docker compose up --detach`
7. run database migrations
   - `python manage.py migrate`
8. create a superuser
   - `python manage.py createsuperuser`  
9. run the local server
   - `python manage.py runserver`

Once the server is running, you can access it from http://localhost:8000

From there, you can begin adding the basic content, such as:

- Home page
- Community Page
  - Contact(s)
- Magazine Index
  - Magazine Issue(s)
    - Magazine Article(s)
- Tags Index
- etc.

If you have any difficulty or questions, please [open a support ticket](https://github.com/WesternFriend/WF-website/issues).

## pgAdmin database access

We include pgAdmin in our Docker compose setup, which can be useful for exploring the database. the pgAdmin service should be running on localhost:5050 with the username and password being defined in the `docker-compose.yaml` file.

## Docker UI alternative

If you would like to use an alternative to Docker/Docker UI, try running [Colima](https://github.com/abiosoft/colima). Once Colima is installed, run the following command before running `docker compose up --detach`.

```sh
colima start
```
