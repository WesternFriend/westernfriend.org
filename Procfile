release: python manage.py migrate && python manage.py createcachetable
web: python manage.py migrate && gunicorn core.wsgi --log-file -
