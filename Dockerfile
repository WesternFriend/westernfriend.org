FROM python:3.6
LABEL maintainer="hello@wagtail.io"

ENV PYTHONUNBUFFERED 1
ENV DJANGO_ENV dev

COPY ./requirements.txt /code/requirements.txt
RUN pip install -r /code/requirements.txt
RUN poetry config virtualenvs.create false
RUN poetry install --no-dev
RUN pip install gunicorn

COPY . /code/
WORKDIR /code/

RUN python manage.py migrate

RUN useradd wagtail
RUN chown -R wagtail /code
USER wagtail

EXPOSE 8000
CMD exec gunicorn wf_website.wsgi:application --bind 0.0.0.0:8000 --workers 3
