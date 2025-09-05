#!/bin/bash
# SHEBANG: Tells the system to run this script with bash shell

# ERROR HANDLING SETUP
set -e
# Exit immediately if any command fails - prevents deployment with broken state

# COMMAND LINE ARGUMENT PROCESSING
ENVIRONMENT=${1:-staging}
# First argument: target environment (defaults to "staging" if not provided)
# Examples: ./deploy.sh production -> ENVIRONMENT="production"
#          ./deploy.sh            -> ENVIRONMENT="staging"

IMAGE_TAG=${2:-latest}
# Second argument: Docker image tag to deploy (defaults to "latest")
# Examples: ./deploy.sh production v1.2.3 -> IMAGE_TAG="v1.2.3"
#          ./deploy.sh production        -> IMAGE_TAG="latest"

echo "Deploying to $ENVIRONMENT environment..."

# DEPLOYMENT LOGIC: ENVIRONMENT-SPECIFIC CONFIGURATIONS
case $ENVIRONMENT in
  # PRODUCTION DEPLOYMENT BRANCH
  "production")
    # Production deployment to Google Cloud Run
    echo "Deploying to Google Cloud Run..."
    
    # Deploy to Google Cloud Run with production specifications
    gcloud run deploy my-app \
      --image gcr.io/my-project/my-app:$IMAGE_TAG \      # Container image location
      --platform managed \                              # Use Google's managed platform
      --region us-central1 \                           # Geographic deployment region
      --allow-unauthenticated \                        # Allow public access
      --set-env-vars "DATABASE_URL=${PROD_DATABASE_URL}" \  # Production database connection
      --memory 512Mi \                                 # Allocate 512MB RAM
      --cpu 1 \                                       # Allocate 1 CPU core
      --min-instances 1 \                             # Always keep 1 instance running
      --max-instances 10 \                            # Scale up to 10 instances max
      --concurrency 80                                # Handle 80 requests per instance
    
    # Update traffic routing to new deployment
    gcloud run services update-traffic my-app \
      --to-latest \                                   # Route all traffic to newest version
      --region us-central1
    ;;
  
  # STAGING DEPLOYMENT BRANCH
  "staging")
    # Staging deployment with reduced resources
    echo "Deploying to staging environment..."
    
    # Deploy staging version with different resource allocation
    gcloud run deploy my-app-staging \
      --image gcr.io/my-project/my-app:$IMAGE_TAG \
      --platform managed \
      --region us-central1 \
      --set-env-vars "DATABASE_URL=${STAGING_DATABASE_URL}" \  # Staging database
      --memory 256Mi \                                # Less memory for staging
      --cpu 0.5                                      # Half CPU allocation
    ;;
  
  # ERROR HANDLING: INVALID ENVIRONMENT
  *)
    # Handle unrecognized environment names
    echo "Unknown environment: $ENVIRONMENT"
    echo "Usage: $0 [production|staging] [image_tag]"
    exit 1  # Exit with error status
    ;;
esac

echo "Deployment to $ENVIRONMENT completed successfully!"

# POST-DEPLOYMENT VERIFICATION
# Run health check to verify deployment success
echo "Running post-deployment health check..."

sleep 30  # Wait 30 seconds for service to fully initialize

# ENVIRONMENT-SPECIFIC HEALTH CHECK URLS
if [ "$ENVIRONMENT" == "production" ]; then
  HEALTH_URL="https://my-app-hash-uc.a.run.app/health"      # Production health endpoint
else
  HEALTH_URL="https://my-app-staging-hash-uc.a.run.app/health"  # Staging health endpoint
fi

# EXECUTE HEALTH CHECK
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)
# curl options:
# -s: Silent mode (no progress output)
# -o /dev/null: Discard response body
# -w "%{http_code}": Output only the HTTP status code

# VERIFY HEALTH CHECK RESULTS
if [ "$HTTP_STATUS" == "200" ]; then
  echo "✅ Health check passed!"          # Success: HTTP 200 OK
else
  echo "❌ Health check failed with status: $HTTP_STATUS"  # Failure: non-200 status
  exit 1  # Exit with error to indicate deployment verification failed
fi 