# Western Friend website (prototype)
Prototype website for [Western Friend](https://westernfriend.org), part of the Religious Society of Friends.

## Development
This project is built with [Python](https://www.python.org/), [Django](https://www.djangoproject.com/), and [Wagtail CMS](https://wagtail.io/). 

In order to get started contributing, set up a development environment with the following steps:

1. clone this repository
    - `git clone git@github.com:WesternFriend/WF-website.git`
2. change into cloned directory and project folder (`wf_website`)
    - `cd WF-website/wf_website`
3. create a Python environment
    - `python -m venv env`
4. activate the environment
    - `source env/bin/activate`
5. install the requirements
    - `pip install -r requirements.txt
6. run migrations
    - `python manage.py migrate`
7. create a super user
    - `python manage.py createsuperuser`
8. run the project
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


