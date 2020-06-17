# Western Friend website (prototype)

Prototype website for [Western Friend](https://westernfriend.org), part of the Religious Society of Friends.

## Development

This project is built with [Python](https://www.python.org/), [Django](https://www.djangoproject.com/), and [Wagtail CMS](https://wagtail.io/). We now use [Poetry](https://python-poetry.org/) for dependency / virtual environment management. After [installing Poetry](https://python-poetry.org/docs/#installation), you can set up a development environment with the following steps:

1. clone this repository
   - `git clone git@github.com:WesternFriend/WF-website.git`
2. change into cloned directory and project folder (`wf_website`)
   - `cd WF-website/wf_website`
3. activate a Poetry virtual environment
   - `poetry shell`
4. install the project dependencies
   - `poetry install`
5. run the local server
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

## Attribution

Portions of code for the Store and Cart apps comes used, with permission, from the book [Django 2 by Example](https://www.packtpub.com/application-development/django-2-example) by Antonio Melé.
