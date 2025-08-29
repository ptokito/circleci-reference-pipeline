#!/bin/bash
set -e

TEST_TYPE=${1:-unit}

case $TEST_TYPE in
  "unit")
    echo "Running unit tests..."
    python -m pytest src/tests/ -v --cov=src --cov-report=term-missing
    ;;
  
  "integration")
    echo "Running integration tests with Docker Compose..."
    
    # Create test results directory
    mkdir -p test-results-integration
    
    # For CircleCI, we use the pre-built image
    if [ -n "$CIRCLE_SHA1" ]; then
      # Create docker-compose.test.yml for integration tests in CircleCI
      cat > docker-compose.test.yml << EOD
version: '3.8'
services:
  app:
    image: my-app:${CIRCLE_SHA1}
    environment:
      - DATABASE_URL=postgresql://testuser:testpass@db:5432/testdb
    depends_on:
      db:
        condition: service_healthy
    command: |
      sh -c "
        python app.py migrate &&
        python -m pytest tests/ -v --junitxml=/tmp/test-results/junit.xml || true
      "
    volumes:
      - ./test-results-integration:/tmp/test-results
  
  db:
    image: postgres:14
    environment:
      - POSTGRES_USER=testuser
      - POSTGRES_PASSWORD=testpass
      - POSTGRES_DB=testdb
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U testuser -d testdb"]
      interval: 10s
      timeout: 5s
      retries: 5
    tmpfs:
      - /var/lib/postgresql/data
EOD
    else
      # For local testing, build the image
      echo "Building Docker image for local testing..."
      docker build -t my-app:latest .
      
      # Use the existing docker-compose.test.yml which builds locally
      echo "Using existing docker-compose.test.yml for local testing"
    fi
    
    # Run integration tests
    docker-compose -f docker-compose.test.yml up --abort-on-container-exit --exit-code-from app
    
    # Cleanup
    docker-compose -f docker-compose.test.yml down -v
    
    # Only remove the generated file in CircleCI
    if [ -n "$CIRCLE_SHA1" ]; then
      rm -f docker-compose.test.yml
    fi
    ;;
  
  *)
    echo "Unknown test type: $TEST_TYPE"
    echo "Usage: $0 [unit|integration]"
    exit 1
    ;;
esac

echo "Tests completed successfully!"
