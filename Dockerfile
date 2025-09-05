# MULTI-STAGE DOCKER BUILD STRATEGY
# This approach creates smaller, more secure production images by separating 
# build dependencies from runtime dependencies

# STAGE 1: BUILDER - Compilation and dependency installation
FROM python:3.11-slim as builder
# Start with minimal Python image for building
# 'as builder' creates a named stage we can reference later

WORKDIR /app
# Set working directory inside the container

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*
# Clean up package lists to reduce image size

# Copy requirements and install dependencies
COPY src/requirements.txt .
# Copy only requirements file first (Docker layer caching optimization)
RUN pip install --no-cache-dir -r requirements.txt
# Install Python packages, --no-cache-dir saves space

# STAGE 2: PRODUCTION - Runtime environment only
FROM python:3.11-slim as production
# Start fresh with clean slim image for production
# This excludes build tools, reducing attack surface and size

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*
# Only install what's needed to run the application

# Copy installed packages from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
# Transfer compiled Python packages without build dependencies

# Copy application code
COPY src/ .
# Copy application source code to container

# Copy test file for integration tests
COPY test_app_working.py .
# Include test file for CI/CD integration testing

# SECURITY: Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser
# Create a restricted user account for running the application
RUN chown -R appuser:appuser /app
# Give the application user ownership of the app directory
USER appuser
# Switch to non-root user (security best practice)

EXPOSE 8000
# Document that the application listens on port 8000
# This is informational - doesn't actually open the port

CMD ["python", "app.py"]
# Default command to run when the container starts