#!/bin/bash
set -e

# Script to preload the Ollama models needed for the application

echo "Setting up required Ollama models..."

# Wait for Ollama service to be ready
echo "Waiting for Ollama service to be ready..."
while ! curl -s http://ollama:11434/api/version > /dev/null; do
    echo "Ollama service not ready yet, waiting..."
    sleep 5
done

echo "Ollama service is ready!"

# Pull the required model
echo "Pulling qwen2.5:1.5b model (this may take some time)..."
ollama pull qwen2.5:1.5b

echo "Ollama models setup completed successfully!"