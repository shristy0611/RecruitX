#!/bin/bash
# Start script for RecruitPro AI

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker first."
    exit 1
fi

# Check for Python environment
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate || { echo "Failed to activate virtual environment"; exit 1; }

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Start Docker services if not already running
if ! docker ps | grep -q recruitx_weaviate; then
    echo "Starting Docker services..."
    docker-compose up -d
    
    # Wait for Weaviate to be ready
    echo "Waiting for Weaviate to be ready..."
    for i in {1..12}; do
        if curl -s http://localhost:8080/v1/.well-known/ready > /dev/null; then
            echo "Weaviate is ready."
            break
        fi
        if [ $i -eq 12 ]; then
            echo "Timed out waiting for Weaviate to be ready."
            echo "Check Docker logs with: docker logs recruitx_weaviate"
            exit 1
        fi
        echo "Waiting... ($i/12)"
        sleep 10
    done
    
    # Set up Weaviate schemas
    echo "Setting up Weaviate schemas..."
    python setup_weaviate.py
fi

# Start the API
echo "Starting RecruitPro AI API..."
python main.py
