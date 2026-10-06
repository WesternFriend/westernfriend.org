release: python manage.py migrate && python manage.py createcachetable
web: gunicorn core.wsgi --log-file -
