FROM python:3.8.1-slim-buster
LABEL maintainer="brylie@amble.fi"

ENV PYTHONUNBUFFERED 1
ENV DJANGO_ENV dev
ENV PORT=8000

# Use bash instead of sh
#SHELL ["/bin/bash", "-c"]

# Port used by this container to serve HTTP.
EXPOSE 8000

# Install system packages required by Wagtail and Django.
RUN apt-get update --yes --quiet && apt-get install --yes --quiet --no-install-recommends \
    build-essential \
    libpq-dev \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    libwebp-dev \
    curl \
 && rm -rf /var/lib/apt/lists/*

# We use gunicorn to serve the project
RUN pip install gunicorn
RUN pip install poetry

# Poetry is used for project package management
#RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python

# Note: we don't want Poetry to create a virtual environment
RUN poetry config virtualenvs.create false --local

WORKDIR /app/

COPY . /app

# Install Poetry dependencies
RUN poetry install --no-dev

# Collect static files.
RUN python manage.py collectstatic --noinput --clear

# Run database migrations
RUN python manage.py migrate --noinput

# Run the server
CMD set -xe; gunicorn wf_website.wsgi:application --workers 3
