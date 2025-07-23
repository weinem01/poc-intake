#!/bin/bash

# Frontend deployment script for POC Intake
set -e

PROJECT_ID="${1:-pound-of-cure-dev}"
REGION="us-central1"

echo "🚀 Deploying POC Intake Frontend"
echo "Project: $PROJECT_ID"
echo ""

# Set project
gcloud config set project $PROJECT_ID

# Navigate to frontend directory
cd frontend

echo "📦 Building frontend Docker image..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/poc-intake-frontend

echo ""
echo "🌐 Deploying frontend to Cloud Run..."
gcloud run deploy poc-intake-frontend \
  --image gcr.io/$PROJECT_ID/poc-intake-frontend \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --port 3000 \
  --memory 1Gi \
  --timeout 300 \
  --min-instances 0 \
  --max-instances 10

# Get frontend URL
FRONTEND_URL=$(gcloud run services describe poc-intake-frontend --platform=managed --region=$REGION --format="value(status.url)")

echo ""
echo "✅ Frontend deployed successfully!"
echo "Frontend URL: $FRONTEND_URL"
echo ""
echo "📝 Notes:"
echo "- The frontend will automatically connect to the backend"
echo "- No API URL configuration needed (uses runtime detection)"
echo "- Access the chat with: ${FRONTEND_URL}?id=<base64-encoded-mrn>"
echo ""

# Optional: Update backend CORS if needed
echo "🔧 Checking if backend CORS needs updating..."
BACKEND_URL=$(gcloud run services describe poc-intake-backend --platform=managed --region=$REGION --format="value(status.url)" 2>/dev/null || echo "")

if [ -n "$BACKEND_URL" ]; then
    echo "Found backend at: $BACKEND_URL"
    echo "Updating CORS settings..."
    
    gcloud run services update poc-intake-backend \
      --platform managed \
      --region $REGION \
      --update-env-vars="CORS_ORIGINS=$FRONTEND_URL" \
      --quiet
    
    echo "✅ CORS updated successfully"
else
    echo "⚠️  Backend service not found. Make sure to deploy the backend first."
fi

echo ""
echo "🎉 Frontend deployment completed!"