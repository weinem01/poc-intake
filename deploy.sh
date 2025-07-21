#!/bin/bash

# POC Intake - Google Cloud Deployment Script
# This script deploys both backend and frontend to Google Cloud Run

set -e

# Configuration
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-}"
REGION="us-central1"
BACKEND_SERVICE="poc-intake-backend"
FRONTEND_SERVICE="poc-intake-frontend"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if gcloud is installed and authenticated
check_gcloud() {
    log_info "Checking gcloud installation and authentication..."
    
    if ! command -v gcloud &> /dev/null; then
        log_error "gcloud CLI is not installed. Please install it from: https://cloud.google.com/sdk/docs/install"
        exit 1
    fi
    
    if ! gcloud auth list --filter="status:ACTIVE" --format="value(account)" | grep -q .; then
        log_error "No active gcloud authentication found. Please run: gcloud auth login"
        exit 1
    fi
    
    log_success "gcloud is installed and authenticated"
}

# Set project ID
set_project() {
    if [ -z "$PROJECT_ID" ]; then
        log_info "No PROJECT_ID set. Please enter your Google Cloud Project ID:"
        read -r PROJECT_ID
    fi
    
    log_info "Setting project to: $PROJECT_ID"
    gcloud config set project "$PROJECT_ID"
    
    # Verify project exists
    if ! gcloud projects describe "$PROJECT_ID" &> /dev/null; then
        log_error "Project $PROJECT_ID does not exist or you don't have access to it"
        exit 1
    fi
    
    log_success "Project set successfully"
}

# Enable required APIs
enable_apis() {
    log_info "Enabling required Google Cloud APIs..."
    
    gcloud services enable \
        cloudbuild.googleapis.com \
        run.googleapis.com \
        containerregistry.googleapis.com \
        secretmanager.googleapis.com
    
    log_success "APIs enabled successfully"
}

# Deploy backend
deploy_backend() {
    log_info "Deploying backend to Cloud Run..."
    
    cd backend
    
    # Submit Cloud Build
    gcloud builds submit --config=cloudbuild.yaml
    
    log_success "Backend deployed successfully"
    
    # Get backend URL
    BACKEND_URL=$(gcloud run services describe $BACKEND_SERVICE --platform=managed --region=$REGION --format="value(status.url)")
    log_info "Backend URL: $BACKEND_URL"
    
    cd ..
}

# Deploy frontend
deploy_frontend() {
    log_info "Deploying frontend to Cloud Run..."
    
    cd frontend
    
    # Deploy frontend
    gcloud builds submit --config=cloudbuild.yaml
    
    log_success "Frontend deployed successfully"
    
    # Get frontend URL
    FRONTEND_URL=$(gcloud run services describe $FRONTEND_SERVICE --platform=managed --region=$REGION --format="value(status.url)")
    log_info "Frontend URL: $FRONTEND_URL"
    
    cd ..
}

# Update CORS settings for backend
update_cors() {
    log_info "Updating CORS and environment settings..."
    
    if [ -n "$FRONTEND_URL" ] && [ -n "$BACKEND_URL" ]; then
        # Update backend service with frontend URL for CORS
        gcloud run services update $BACKEND_SERVICE \
            --platform=managed \
            --region=$REGION \
            --set-env-vars="CORS_ORIGINS=$FRONTEND_URL"
        
        # Update frontend service with backend URL
        gcloud run services update $FRONTEND_SERVICE \
            --platform=managed \
            --region=$REGION \
            --set-env-vars="NEXT_PUBLIC_API_URL=$BACKEND_URL"
        
        log_success "CORS and environment settings updated"
    else
        log_warning "URLs not available, skipping environment variable updates"
    fi
}

# Display deployment summary
show_summary() {
    log_success "🎉 Deployment completed successfully!"
    echo ""
    echo "📋 Deployment Summary:"
    echo "─────────────────────"
    echo "Project ID: $PROJECT_ID"
    echo "Region: $REGION"
    echo ""
    
    if [ -n "$BACKEND_URL" ]; then
        echo "🚀 Backend Service: $BACKEND_URL"
    fi
    
    if [ -n "$FRONTEND_URL" ]; then
        echo "🌐 Frontend Application: $FRONTEND_URL"
    fi
    
    echo ""
    echo "💡 Next Steps:"
    echo "• Test both services to ensure they're working correctly"
    echo "• Set up domain mapping if needed"
    echo "• Configure environment variables in Cloud Run console"
    echo "• Set up monitoring and alerting"
}

# Main deployment flow
main() {
    log_info "🚀 Starting POC Intake deployment to Google Cloud..."
    echo ""
    
    check_gcloud
    set_project
    enable_apis
    
    # Deploy services
    deploy_backend
    deploy_frontend
    update_cors
    
    # Show summary
    show_summary
}

# Run main function
main "$@"