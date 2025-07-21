# POC Intake - Google Cloud Deployment Guide

This guide walks through deploying the POC Intake application (FastAPI backend + Next.js frontend) to Google Cloud Platform using Cloud Run.

## Prerequisites

1. **Google Cloud Account**: Set up a GCP account with billing enabled
2. **Google Cloud CLI**: Install and authenticate gcloud CLI
3. **Project Setup**: Create a new GCP project or use an existing one
4. **Required APIs**: Enable the following APIs (done automatically by the script):
   - Cloud Build API
   - Cloud Run API
   - Container Registry API
   - Secret Manager API

## Quick Deployment

The easiest way to deploy is using the provided deployment script:

```bash
# Make the script executable (if not already)
chmod +x deploy.sh

# Run the deployment
./deploy.sh
```

The script will:
1. Check gcloud installation and authentication
2. Enable required APIs
3. Deploy the backend to Cloud Run
4. Deploy the frontend to Cloud Run
5. Configure CORS settings
6. Display deployment URLs

## Manual Deployment

If you prefer to deploy manually or need more control:

### 1. Set up Environment Variables

```bash
export PROJECT_ID="your-gcp-project-id"
export REGION="us-central1"
```

### 2. Enable Required APIs

```bash
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    containerregistry.googleapis.com \
    secretmanager.googleapis.com
```

### 3. Deploy Backend

```bash
cd backend

# Build and deploy using Cloud Build
gcloud builds submit --config=cloudbuild.yaml

# Alternatively, build and deploy manually:
# gcloud builds submit --tag gcr.io/$PROJECT_ID/poc-intake-backend
# gcloud run deploy poc-intake-backend \
#   --image gcr.io/$PROJECT_ID/poc-intake-backend \
#   --platform managed \
#   --region $REGION \
#   --allow-unauthenticated
```

### 4. Deploy Frontend

```bash
cd frontend

# Build and deploy using Cloud Build
gcloud builds submit --config=cloudbuild.yaml

# Set the backend URL for the frontend
BACKEND_URL=$(gcloud run services describe poc-intake-backend --platform=managed --region=$REGION --format="value(status.url)")

gcloud run services update poc-intake-frontend \
  --platform managed \
  --region $REGION \
  --set-env-vars="NEXT_PUBLIC_API_URL=$BACKEND_URL"
```

### 5. Update CORS Settings

```bash
FRONTEND_URL=$(gcloud run services describe poc-intake-frontend --platform=managed --region=$REGION --format="value(status.url)")

gcloud run services update poc-intake-backend \
  --platform managed \
  --region $REGION \
  --set-env-vars="CORS_ORIGINS=$FRONTEND_URL"
```

## Environment Variables & Secrets

### Backend Environment Variables

Set these in Cloud Run console or using gcloud:

```bash
# Required secrets (store in Secret Manager)
# Note: OpenAI key secret is named "open-ai-key" to match existing setup
gcloud secrets create open-ai-key --data-file=- <<< "your-openai-key"
gcloud secrets create supabase-url --data-file=- <<< "your-supabase-url"
gcloud secrets create supabase-service-role-key --data-file=- <<< "your-supabase-key"
gcloud secrets create charm-client-id --data-file=- <<< "your-charm-client-id"
gcloud secrets create charm-client-secret --data-file=- <<< "your-charm-client-secret"
gcloud secrets create charm-refresh-token --data-file=- <<< "your-charm-refresh-token"
gcloud secrets create charm-api-key --data-file=- <<< "your-charm-api-key"
gcloud secrets create charm-auth-base-url --data-file=- <<< "your-charm-auth-url"
gcloud secrets create perplexity-api-key --data-file=- <<< "your-perplexity-key"

# Grant Cloud Run service account access to secrets
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$(gcloud run services describe poc-intake-backend --platform=managed --region=$REGION --format='value(spec.template.spec.serviceAccountName)')" \
  --role="roles/secretmanager.secretAccessor"
```

### Frontend Environment Variables

```bash
gcloud run services update poc-intake-frontend \
  --platform managed \
  --region $REGION \
  --set-env-vars="NEXT_PUBLIC_API_URL=https://your-backend-url"
```

## Monitoring & Logs

### View Logs

```bash
# Backend logs
gcloud logs tail --filter="resource.type=cloud_run_revision AND resource.labels.service_name=poc-intake-backend"

# Frontend logs
gcloud logs tail --filter="resource.type=cloud_run_revision AND resource.labels.service_name=poc-intake-frontend"
```

### Service URLs

```bash
# Get backend URL
gcloud run services describe poc-intake-backend --platform=managed --region=$REGION --format="value(status.url)"

# Get frontend URL
gcloud run services describe poc-intake-frontend --platform=managed --region=$REGION --format="value(status.url)"
```

## Scaling & Performance

### Configure Scaling

```bash
# Backend scaling
gcloud run services update poc-intake-backend \
  --platform managed \
  --region $REGION \
  --min-instances=0 \
  --max-instances=10 \
  --concurrency=80

# Frontend scaling
gcloud run services update poc-intake-frontend \
  --platform managed \
  --region $REGION \
  --min-instances=0 \
  --max-instances=5 \
  --concurrency=100
```

### Resource Allocation

```bash
# Backend resources
gcloud run services update poc-intake-backend \
  --platform managed \
  --region $REGION \
  --memory=1Gi \
  --cpu=1

# Frontend resources
gcloud run services update poc-intake-frontend \
  --platform managed \
  --region $REGION \
  --memory=512Mi \
  --cpu=1
```

## Custom Domain (Optional)

### Set up Domain Mapping

```bash
# Map custom domain
gcloud run domain-mappings create \
  --service poc-intake-frontend \
  --domain your-domain.com \
  --platform managed \
  --region $REGION

# Map API subdomain
gcloud run domain-mappings create \
  --service poc-intake-backend \
  --domain api.your-domain.com \
  --platform managed \
  --region $REGION
```

## CI/CD with Cloud Build

### Automatic Deployment

Set up Cloud Build triggers for automatic deployment:

```bash
# Backend trigger
gcloud builds triggers create github \
  --repo-name=your-repo \
  --repo-owner=your-username \
  --branch-pattern="^main$" \
  --build-config="backend/cloudbuild.yaml" \
  --include-logs-with-status

# Frontend trigger
gcloud builds triggers create github \
  --repo-name=your-repo \
  --repo-owner=your-username \
  --branch-pattern="^main$" \
  --build-config="frontend/cloudbuild.yaml" \
  --include-logs-with-status
```

## Troubleshooting

### Common Issues

1. **Authentication Errors**: Ensure gcloud is authenticated and has proper permissions
2. **Secret Manager Access**: Verify the Cloud Run service account has Secret Manager access
3. **CORS Issues**: Check that frontend URL is properly set in backend CORS configuration
4. **Memory Limits**: Increase memory allocation if services are hitting limits
5. **Cold Starts**: Set min-instances > 0 for faster response times

### Debug Commands

```bash
# Check service status
gcloud run services describe poc-intake-backend --platform=managed --region=$REGION

# View recent logs
gcloud logs read --filter="resource.type=cloud_run_revision" --limit=50

# Test service health
curl -f https://your-backend-url/health || echo "Backend health check failed"
```

## Cost Optimization

### Recommendations

1. Use min-instances=0 for development to avoid idle costs
2. Set appropriate CPU and memory limits
3. Monitor usage with Cloud Monitoring
4. Use Cloud Run's pay-per-request pricing model
5. Implement proper caching strategies

## Security

### Best Practices

1. Store all secrets in Secret Manager
2. Use IAM roles with least privilege
3. Enable Cloud Armor for DDoS protection
4. Implement proper CORS configuration
5. Use HTTPS for all communications
6. Regularly update dependencies

For more information, see the [Cloud Run documentation](https://cloud.google.com/run/docs).