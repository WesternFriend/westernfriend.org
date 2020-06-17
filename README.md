# Western Friend website (prototype)
<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->
[![All Contributors](https://img.shields.io/badge/all_contributors-1-orange.svg?style=flat-square)](#contributors-)
<!-- ALL-CONTRIBUTORS-BADGE:END -->

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

## Contributors ✨

Thanks goes to these wonderful people ([emoji key](https://allcontributors.org/docs/en/emoji-key)):

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tr>
    <td align="center"><a href="http://nehemiasec.com"><img src="https://avatars3.githubusercontent.com/u/5385440?v=4" width="100px;" alt=""/><br /><sub><b>N Eliseo S Carranza</b></sub></a><br /><a href="https://github.com/WesternFriend/WF-website/commits?author=NehemiasEC" title="Documentation">📖</a> <a href="https://github.com/WesternFriend/WF-website/issues?q=author%3ANehemiasEC" title="Bug reports">🐛</a></td>
  </tr>
</table>

<!-- markdownlint-enable -->
<!-- prettier-ignore-end -->
<!-- ALL-CONTRIBUTORS-LIST:END -->

This project follows the [all-contributors](https://github.com/all-contributors/all-contributors) specification. Contributions of any kind welcome!