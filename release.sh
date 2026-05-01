#!/bin/bash
# Release script - runs migrations before starting the app
# Used by deployment platforms like Render

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Deployment setup complete!"
