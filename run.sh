#!/bin/bash
# Quick launcher for GL100 Manager

# Change to script directory
cd "$(dirname "$0")"

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating it..."
    python -m venv venv
    ./venv/bin/pip install -r requirements.txt
    ./venv/bin/pip install -e .
fi

# Run the application
./venv/bin/PyMooerLooperManager
