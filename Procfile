release: python manage.py migrate && python manage.py createcachetable django_cache
web: gunicorn core.wsgi --log-file -
