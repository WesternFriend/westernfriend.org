FROM python:3.8.1-slim-buster
LABEL maintainer="brylie@amble.fi"

ENV PYTHONUNBUFFERED 1
ENV DJANGO_ENV dev
ENV PORT=8000

# Port used by this container to serve HTTP.
EXPOSE 8000

# Install system packages required by Wagtail and Django.
RUN apt-get update --yes --quiet && apt-get install --yes --quiet --no-install-recommends \
    build-essential \
    libpq-dev \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    libwebp-dev \
 && rm -rf /var/lib/apt/lists/*

# We use gunicorn to serve the project
RUN pip install gunicorn

# Poetry is used for project package management
RUN pip install poetry

# Add user that will be used in the container.
RUN useradd wagtail

# Copy all files to work directory and change ownership
WORKDIR /app/

# Set directory permissions
RUN chown wagtail:wagtail /app
COPY --chown=wagtail:wagtail . /app

# Use user "wagtail" to run the build commands below
# and the server itself.
USER wagtail

# Install Poetry dependencies
# Note: we don't want Poetry to create a virtual environment
RUN poetry config virtualenvs.create false --local
RUN poetry install --no-dev

# Collect static files.
RUN python manage.py collectstatic --noinput --clear

# Run database migrations
RUN python manage.py migrate --noinput

# Run the server
CMD set -xe; gunicorn wf_website.wsgi:application --workers 3
