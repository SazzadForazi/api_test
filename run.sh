#!/bin/bash
# Startup script for Mock Sandbox API

# Colors for log messages
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0;39m'

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${BLUE}Virtual environment not found. Setting up...${NC}"
    python3 -m venv venv
    ./venv/bin/pip install -r requirements.txt
fi

# Run tests if requested
if [ "$1" == "test" ]; then
    echo -e "${GREEN}Running pytest integration tests...${NC}"
    ./venv/bin/pytest -v test_main.py
    exit $?
fi

# Start the uvicorn app
echo -e "${GREEN}Starting Mock Testing API Server on http://127.0.0.1:8000 ...${NC}"
echo -e "${GREEN}Open http://127.0.0.1:8000/docs for Swagger Interactive Documentation.${NC}"
./venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
