@echo off
REM POC Intake - Google Cloud Deployment Script for Windows
REM This script deploys both backend and frontend to Google Cloud Run

echo 🚀 Starting POC Intake deployment to Google Cloud...
echo.

REM Check if gcloud is installed
gcloud --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ ERROR: gcloud CLI is not installed or not in PATH
    echo Please install it from: https://cloud.google.com/sdk/docs/install
    pause
    exit /b 1
)

REM Check if authenticated
for /f "tokens=*" %%i in ('gcloud auth list --filter="status:ACTIVE" --format="value(account)"') do set ACCOUNT=%%i
if "%ACCOUNT%"=="" (
    echo ❌ ERROR: No active gcloud authentication found
    echo Please run: gcloud auth login
    pause
    exit /b 1
)

echo ✅ gcloud is installed and authenticated as: %ACCOUNT%
echo.

REM Get project ID
if "%GOOGLE_CLOUD_PROJECT%"=="" (
    set /p PROJECT_ID="Enter your Google Cloud Project ID: "
) else (
    set PROJECT_ID=%GOOGLE_CLOUD_PROJECT%
)

echo 📋 Setting project to: %PROJECT_ID%
gcloud config set project %PROJECT_ID%

REM Verify project exists
gcloud projects describe %PROJECT_ID% >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ ERROR: Project %PROJECT_ID% does not exist or you don't have access
    pause
    exit /b 1
)

echo ✅ Project set successfully
echo.

REM Enable required APIs
echo 🔧 Enabling required Google Cloud APIs...
gcloud services enable cloudbuild.googleapis.com run.googleapis.com containerregistry.googleapis.com secretmanager.googleapis.com

echo ✅ APIs enabled successfully
echo.

REM Deploy backend
echo 🚀 Deploying backend to Cloud Run...
cd backend
gcloud builds submit --config=cloudbuild.yaml
if %errorlevel% neq 0 (
    echo ❌ ERROR: Backend deployment failed
    pause
    exit /b 1
)
cd ..

echo ✅ Backend deployed successfully
echo.

REM Get backend URL
for /f "tokens=*" %%i in ('gcloud run services describe poc-intake-backend --platform=managed --region=us-central1 --format="value(status.url)"') do set BACKEND_URL=%%i
echo 📋 Backend URL: %BACKEND_URL%
echo.

REM Deploy frontend
echo 🌐 Deploying frontend to Cloud Run...
cd frontend
gcloud builds submit --config=cloudbuild.yaml
if %errorlevel% neq 0 (
    echo ❌ ERROR: Frontend deployment failed
    pause
    exit /b 1
)
cd ..

echo ✅ Frontend deployed successfully
echo.

REM Get frontend URL
for /f "tokens=*" %%i in ('gcloud run services describe poc-intake-frontend --platform=managed --region=us-central1 --format="value(status.url)"') do set FRONTEND_URL=%%i
echo 📋 Frontend URL: %FRONTEND_URL%
echo.

REM Update CORS settings
echo 🔧 Updating CORS settings...
gcloud run services update poc-intake-backend --platform=managed --region=us-central1 --set-env-vars="CORS_ORIGINS=%FRONTEND_URL%"
gcloud run services update poc-intake-frontend --platform=managed --region=us-central1 --set-env-vars="NEXT_PUBLIC_API_URL=%BACKEND_URL%"

echo ✅ CORS settings updated
echo.

REM Display summary
echo 🎉 Deployment completed successfully!
echo.
echo 📋 Deployment Summary:
echo ─────────────────────
echo Project ID: %PROJECT_ID%
echo Region: us-central1
echo.
echo 🚀 Backend Service: %BACKEND_URL%
echo 🌐 Frontend Application: %FRONTEND_URL%
echo.
echo 💡 Next Steps:
echo • Test both services to ensure they're working correctly
echo • Set up domain mapping if needed
echo • Configure environment variables in Cloud Run console
echo • Set up monitoring and alerting
echo.
pause