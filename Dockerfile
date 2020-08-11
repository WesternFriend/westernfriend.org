FROM python:3.8.1-slim-buster
LABEL maintainer="brylie@amble.fi"

ENV PYTHONUNBUFFERED 1
ENV DJANGO_ENV dev

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

WORKDIR /app/
COPY . /app

# Note: we don't want Poetry to create a virtual environment
RUN poetry config virtualenvs.create false --local
# Install Poetry dependencies
RUN poetry install --no-dev

# Collect static files.
RUN python manage.py collectstatic --noinput --clear

# Run database migrations
RUN python manage.py migrate --noinput

RUN useradd wagtail
RUN chown -R wagtail /app

USER wagtail

# Port used by this container to serve HTTP.
EXPOSE 8000

# Run the server
CMD set -xe; gunicorn wf_website.wsgi:application --workers 3
