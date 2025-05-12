#!/bin/bash

# Exit on error
set -e

echo "Building Gemma 3 model for Docker Desktop"

# Check for Hugging Face token
if [ -z "$HF_TOKEN" ]; then
    read -p "Enter your Hugging Face token (or press Enter to skip): " TOKEN
    if [ ! -z "$TOKEN" ]; then
        export HF_TOKEN=$TOKEN
    else
        echo "Warning: No Hugging Face token provided. You may encounter issues accessing the Gemma model."
    fi
fi

# Build the Docker image
echo "Building Docker image for Gemma 3..."
docker-compose -f docker-compose.gemma.yml build

# Run the model
echo "Starting Gemma 3 model..."
docker-compose -f docker-compose.gemma.yml up -d

echo "Waiting for the model to start..."
sleep 5

# Check if model is running
MAX_RETRIES=10
RETRIES=0
while [ $RETRIES -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:8000/health > /dev/null; then
        echo "Gemma 3 model is now running and can be used with Docker Desktop Models!"
        echo "To use it in your application, update your .env file with:"
        echo "LOCAL_LLM_URL=http://localhost:8000"
        echo "LOCAL_LLM_MODEL=gemma-3-4b"
        exit 0
    fi
    echo "Waiting for model to start... ($((RETRIES+1))/$MAX_RETRIES)"
    RETRIES=$((RETRIES+1))
    sleep 10
done

echo "Model failed to start within expected time. Check logs with: docker logs recruitx-gemma3-model"
exit 1 