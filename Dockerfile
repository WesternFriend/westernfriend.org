FROM python:3.9
LABEL maintainer="brylie@amble.fi"

ENV PYTHONUNBUFFERED 1
ENV DJANGO_ENV dev
ENV POETRY_HOME=/opt/poetry

# Install system packages required by Wagtail and Django.
RUN apt-get update --yes --quiet && apt-get install --yes --quiet --no-install-recommends \
    build-essential \
    libpq-dev \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    libwebp-dev \
    && rm -rf /var/lib/apt/lists/*

# Poetry is used to manage dependencies
RUN pip install poetry
RUN python3 -m venv $POETRY_HOME
RUN $POETRY_HOME/bin/pip install poetry==1.2.0

# We use gunicorn to serve the project
RUN pip install gunicorn

WORKDIR /app/
# Cache dependencies
COPY poetry.lock pyproject.toml /app/

# Note: we don't want Poetry to create a virtual environment
# since it has led to broken builds
RUN $POETRY_HOME/bin/poetry config virtualenvs.create false

# Install Poetry dependencies
RUN $POETRY_HOME/bin/poetry install --only main --no-ansi

# Copy app files
COPY . /app

RUN useradd wagtail
RUN chown -R wagtail /app

USER wagtail

# Port used by this container to serve HTTP.
EXPOSE 8000

# Run the server
CMD set -xe; gunicorn --worker-tmp-dir /dev/shm core.wsgi:application --workers 3
