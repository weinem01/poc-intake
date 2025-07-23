#!/bin/bash

# Deployment script with proper secret handling
set -e

PROJECT_ID="${1:-pound-of-cure-dev}"
REGION="us-central1"

echo "🚀 Deploying POC Intake with Secret Manager setup"
echo "Project: $PROJECT_ID"
echo ""

# Set project
gcloud config set project $PROJECT_ID

# Get project number for service account
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

echo "📋 Service Account: $SERVICE_ACCOUNT"
echo ""

# Check if open-ai-key secret exists
echo "🔍 Checking for open-ai-key secret..."
if gcloud secrets describe open-ai-key >/dev/null 2>&1; then
    echo "✅ Secret 'open-ai-key' exists"
    
    # Grant access to the secret
    echo "🔐 Granting service account access to secret..."
    gcloud secrets add-iam-policy-binding open-ai-key \
        --member="serviceAccount:${SERVICE_ACCOUNT}" \
        --role="roles/secretmanager.secretAccessor" \
        --quiet
    
    echo "✅ Access granted"
else
    echo "❌ Secret 'open-ai-key' not found!"
    echo "Please create it with: gcloud secrets create open-ai-key --data-file=- <<< 'your-api-key'"
    exit 1
fi

# Deploy backend
echo ""
echo "📦 Building and deploying backend..."
cd backend

# Build the image
gcloud builds submit --tag gcr.io/$PROJECT_ID/poc-intake-backend

# Deploy with explicit service account
gcloud run deploy poc-intake-backend \
  --image gcr.io/$PROJECT_ID/poc-intake-backend \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --port 8080 \
  --memory 1Gi \
  --timeout 300 \
  --service-account=$SERVICE_ACCOUNT \
  --set-env-vars="ENVIRONMENT=production,GCP_PROJECT_ID=$PROJECT_ID"

# Get backend URL
BACKEND_URL=$(gcloud run services describe poc-intake-backend --platform=managed --region=$REGION --format="value(status.url)")
echo "✅ Backend deployed at: $BACKEND_URL"

cd ..

# Deploy frontend
echo ""
echo "🌐 Building and deploying frontend..."
cd frontend

# Build with backend URL
gcloud builds submit \
  --tag gcr.io/$PROJECT_ID/poc-intake-frontend \
  --substitutions=_BACKEND_URL=$BACKEND_URL

gcloud run deploy poc-intake-frontend \
  --image gcr.io/$PROJECT_ID/poc-intake-frontend \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --port 3000 \
  --memory 1Gi \
  --timeout 300 \
  --set-env-vars="NODE_ENV=production,NEXT_PUBLIC_API_URL=$BACKEND_URL"

# Get frontend URL
FRONTEND_URL=$(gcloud run services describe poc-intake-frontend --platform=managed --region=$REGION --format="value(status.url)")
echo "✅ Frontend deployed at: $FRONTEND_URL"

cd ..

# Update CORS
echo ""
echo "🔧 Updating CORS settings..."
gcloud run services update poc-intake-backend \
  --platform managed \
  --region $REGION \
  --update-env-vars="CORS_ORIGINS=$FRONTEND_URL"

echo ""
echo "🎉 Deployment completed!"
echo "Frontend: $FRONTEND_URL"
echo "Backend: $BACKEND_URL"
echo ""
echo "📝 Note: Make sure you have these secrets in Secret Manager:"
echo "  - open-ai-key (required)"
echo "  - supabase-url"
echo "  - supabase-service-role-key"
echo "  - charm-* secrets (for Charm API integration)"