#!/usr/bin/env bash
# Railway startup script - runs migrations then starts gunicorn

set -e

echo "Running database migrations..."
python manage.py migrate --no-input

echo "Collecting static files..."
python manage.py collectstatic --no-input

# Create superuser only if password is set
if [ -n "$SUPERUSER_PASSWORD" ]; then
    echo "Creating superuser if needed..."
    python manage.py create_superuser_if_none || echo "Superuser creation skipped or failed"
else
    echo "SUPERUSER_PASSWORD not set, skipping superuser creation"
fi

echo "Starting gunicorn..."
exec gunicorn mathcourses.wsgi --log-file -
