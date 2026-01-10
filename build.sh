#!/usr/bin/env bash
# exit on error
set -o errexit

# Collect static files
python manage.py collectstatic --no-input

# Run migrations
python manage.py migrate --no-input
