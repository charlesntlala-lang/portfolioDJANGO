release: python manage.py migrate --noinput && python manage.py collectstatic --noinput --clear
web: gunicorn app:app
