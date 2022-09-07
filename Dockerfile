FROM python:3.9
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
    && rm -rf /var/lib/apt/lists/*

# pipx is used to install Poetry
RUN python3 -m pip install --user pipx
RUN python3 -m pipx ensurepath
RUN python3 -m pipx completions
RUN echo "eval \"\$(register-python-argcomplete pipx)\"" >> ~/.bashrc
RUN source ~/.bashrc

# Poetry is used to manage dependencies
RUN pipx install poetry

# We use gunicorn to serve the project
RUN pip install gunicorn

WORKDIR /app/
COPY . /app

# Note: we don't want Poetry to create a virtual environment
# Instead, it should use a local directory
RUN poetry config virtualenvs.create false

# Install Poetry dependencies
RUN poetry install --only main

RUN useradd wagtail
RUN chown -R wagtail /app

USER wagtail

# Port used by this container to serve HTTP.
EXPOSE 8000

# Run the server
CMD set -xe; gunicorn --worker-tmp-dir /dev/shm core.wsgi:application --workers 3
