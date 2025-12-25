#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate --noinput

# Check if sentences need to be imported
# This is a simple check; you might want a more robust way to determine if import is needed.
# For example, checking a specific flag or if Sentence.objects.count() is 0 via a manage.py command.
echo "Checking if data import is needed..."
SENTENCE_COUNT=$(python manage.py shell -c "from flashcards.models import Sentence; print(Sentence.objects.count())")

if [ "$SENTENCE_COUNT" -eq 0 ]; then
    echo "No sentences found in database. Importing data from CSV..."
    # Assuming your CSV file is named '2000_words.csv' and is in the /app/data directory
    # The /app/data directory in the container is mapped to ./data on the host via docker-compose.yml
    CSV_FILE_PATH="/app/data/2000_words.csv"
    if [ -f "$CSV_FILE_PATH" ]; then
        python manage.py import_csv "$CSV_FILE_PATH"
        echo "Data import finished."
    else
        echo "WARNING: CSV file $CSV_FILE_PATH not found. Skipping data import."
    fi
else
    echo "Sentences already exist in the database (Count: $SENTENCE_COUNT). Skipping data import."
fi

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