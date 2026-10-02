#!/bin/sh
set -e

echo "Applying database migrations..."
python manage.py migrate --noinput

if [ "$SEED_DEMO_DATA" = "true" ]; then
    echo "Initializing demo data..."
    python manage.py seed_demo
    echo "Demo data initialization complete."
fi

echo "Starting Django server..."
exec "$@"
