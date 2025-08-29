#!/bin/bash
set -e

ENVIRONMENT=${1:-staging}
IMAGE_TAG=${2:-latest}

echo "Deploying to $ENVIRONMENT environment..."

case $ENVIRONMENT in
  "production")
    # Production deployment to Google Cloud Run
    echo "Deploying to Google Cloud Run..."
    
    gcloud run deploy my-app \
      --image gcr.io/my-project/my-app:$IMAGE_TAG \
      --platform managed \
      --region us-central1 \
      --allow-unauthenticated \
      --set-env-vars "DATABASE_URL=${PROD_DATABASE_URL}" \
      --memory 512Mi \
      --cpu 1 \
      --min-instances 1 \
      --max-instances 10 \
      --concurrency 80
    
    # Update traffic allocation
    gcloud run services update-traffic my-app \
      --to-latest \
      --region us-central1
    ;;
  
  "staging")
    # Staging deployment
    echo "Deploying to staging environment..."
    
    gcloud run deploy my-app-staging \
      --image gcr.io/my-project/my-app:$IMAGE_TAG \
      --platform managed \
      --region us-central1 \
      --set-env-vars "DATABASE_URL=${STAGING_DATABASE_URL}" \
      --memory 256Mi \
      --cpu 0.5
    ;;
  
  *)
    echo "Unknown environment: $ENVIRONMENT"
    echo "Usage: $0 [production|staging] [image_tag]"
    exit 1
    ;;
esac

echo "Deployment to $ENVIRONMENT completed successfully!"

# Run post-deployment health check
echo "Running post-deployment health check..."
sleep 30  # Wait for service to be ready

if [ "$ENVIRONMENT" == "production" ]; then
  HEALTH_URL="https://my-app-hash-uc.a.run.app/health"
else
  HEALTH_URL="https://my-app-staging-hash-uc.a.run.app/health"
fi

HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)
if [ "$HTTP_STATUS" == "200" ]; then
  echo "✅ Health check passed!"
else
  echo "❌ Health check failed with status: $HTTP_STATUS"
  exit 1
fi
