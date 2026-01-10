#!/usr/bin/env bash
# Railway startup script - runs migrations then starts gunicorn

set -e

echo "Running database migrations..."
python manage.py migrate --no-input

echo "Collecting static files..."
python manage.py collectstatic --no-input

echo "Creating superuser if needed..."
python manage.py create_superuser_if_none

echo "Starting gunicorn..."
exec gunicorn mathcourses.wsgi --log-file -
