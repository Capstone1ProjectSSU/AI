#!/bin/bash

# Start the FastAPI server
echo "Starting HiServer FastAPI application..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
