#!/bin/bash

# Start the Celery worker
echo "Starting Celery worker..."
celery -A app.celery_app worker --loglevel=info --concurrency=2
