#!/bin/bash

# Fix CORS for POC Intake
echo "🔧 Updating CORS settings for backend..."

gcloud run services update poc-intake-backend \
  --platform managed \
  --region us-central1 \
  --update-env-vars="CORS_ORIGINS=https://poc-intake-frontend-1023146209184.us-central1.run.app"

echo "✅ CORS settings updated!"
echo ""
echo "The backend will now accept requests from:"
echo "https://poc-intake-frontend-1023146209184.us-central1.run.app"