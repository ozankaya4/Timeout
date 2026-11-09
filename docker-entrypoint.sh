#!/bin/sh
# Container start: apply migrations, seed demo data on an empty database, then serve.
set -e

python manage.py migrate --noinput
python manage.py bootstrap_demo

# One process keeps the per-process AI cache consistent and limits SQLite write contention.
exec gunicorn timeout_pwa.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 1 \
    --threads 8 \
    --timeout 120 \
    --access-logfile -
