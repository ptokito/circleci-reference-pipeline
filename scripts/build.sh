#!/bin/bash
# SHEBANG: Tells the system to run this script with bash shell

# ERROR HANDLING SETUP
set -e
# Exit immediately if any command fails - prevents building with broken state

echo "Building Docker image..."

# GIT COMMIT HASH EXTRACTION FOR IMAGE TAGGING
# This creates unique, traceable tags for each build
if git rev-parse --git-dir > /dev/null 2>&1; then
    # Check if we're in a git repository
    # git rev-parse --git-dir: Returns git directory path if in a repo
    # > /dev/null 2>&1: Suppress output and error messages
    
    COMMIT_HASH=$(git rev-parse --short HEAD 2>/dev/null || echo "local")
    # git rev-parse --short HEAD: Get abbreviated commit hash (7 characters)
    # 2>/dev/null: Suppress error messages
    # || echo "local": If git command fails, use "local" as fallback
else
    # Not in a git repository
    COMMIT_HASH="local"
fi

# IMAGE TAG SELECTION WITH ENVIRONMENT VARIABLE OVERRIDE
IMAGE_TAG=${IMAGE_TAG:-$COMMIT_HASH}
# Use IMAGE_TAG environment variable if set, otherwise use COMMIT_HASH
# This allows manual override: IMAGE_TAG=v1.2.3 ./build.sh

echo "Using image tag: $IMAGE_TAG"

# DOCKER IMAGE BUILD PROCESS
# Build the Docker image using current directory as build context
docker build -t my-app:$IMAGE_TAG .
# -t: Tag the image with name:tag format
# .: Use current directory as build context (where Dockerfile is located)

# CREATE ADDITIONAL TAG FOR CONVENIENCE
docker tag my-app:$IMAGE_TAG my-app:latest
# Creates a second tag "latest" pointing to the same image
# Useful for local development and as a fallback reference

echo "Docker image built successfully: my-app:$IMAGE_TAG"

# POST-BUILD VERIFICATION: SMOKE TEST
echo "Running smoke test..."
docker run --rm --name smoke-test-$$ my-app:$IMAGE_TAG python -c "import app; print('Import successful')"
# docker run options:
# --rm: Automatically remove container when it exits
# --name smoke-test-$$: Give container a unique name using process ID ($$)
# my-app:$IMAGE_TAG: Use the image we just built
# python -c "...": Run Python command to test basic functionality
# import app: Verify the main application module can be imported
# This catches basic issues like missing dependencies or syntax errors

echo "Build completed successfully!"
# Only reached if all previous commands succeeded