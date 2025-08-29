#!/bin/bash
set -e

echo "Building Docker image..."

# Get git commit hash for tagging (with fallback)
if git rev-parse --git-dir > /dev/null 2>&1; then
    COMMIT_HASH=$(git rev-parse --short HEAD 2>/dev/null || echo "local")
else
    COMMIT_HASH="local"
fi

IMAGE_TAG=${IMAGE_TAG:-$COMMIT_HASH}

echo "Using image tag: $IMAGE_TAG"

# Build the Docker image
docker build -t my-app:$IMAGE_TAG .
docker tag my-app:$IMAGE_TAG my-app:latest

echo "Docker image built successfully: my-app:$IMAGE_TAG"

# Run basic smoke test
echo "Running smoke test..."
docker run --rm --name smoke-test-$$ my-app:$IMAGE_TAG python -c "import app; print('Import successful')"

echo "Build completed successfully!"
