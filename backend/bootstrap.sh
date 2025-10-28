#!/bin/bash

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Load environment variables from .env file
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
else
    echo "Warning: .env file not found. Please create one from .env.example"
    exit 1
fi

# Start the server using environment variables
uvicorn main:app --reload --host ${BACKEND_HOST:-0.0.0.0} --port ${BACKEND_PORT:-3009}
