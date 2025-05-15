#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate --noinput

# Collect static files (if you have static files to be served by Django or a web server)
# echo "Collecting static files..."
# python manage.py collectstatic --noinput

# Check the first argument to the script
if [ "$1" = "run_server" ]; then
    # Start Django development server
    echo "Starting Django development server..."
    exec python manage.py runserver 0.0.0.0:8000
elif [ "$1" = "gunicorn" ]; then
    # Start Gunicorn (production server)
    # Ensure gunicorn is in requirements.txt
    echo "Starting Gunicorn..."
    exec gunicorn spanish_anki_project.wsgi:application --bind 0.0.0.0:8000 --workers 3
else
    # Execute the command passed to the script
    exec "$@"
fi 