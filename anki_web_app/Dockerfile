# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    dos2unix \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project code
COPY . /app/

# Expose port 8000 for the Django app
EXPOSE 8000

# Command to run the application
# For development, we can use runserver. For production, gunicorn is preferred.
# CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
# The entrypoint script will handle migrations and starting the server.
COPY ./entrypoint.sh /app/entrypoint.sh
# Ensure correct line endings and executable permission for the entrypoint script
RUN dos2unix /app/entrypoint.sh
RUN chmod 755 /app/entrypoint.sh
ENTRYPOINT ["/bin/sh", "/app/entrypoint.sh"]
CMD ["run_server"] 