#!/bin/bash
# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
