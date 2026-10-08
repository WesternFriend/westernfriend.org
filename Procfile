release: python manage.py migrate && python manage.py createcachetable django_cache
web: python manage.py migrate && gunicorn core.wsgi --log-file -
