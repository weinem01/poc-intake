#!/bin/bash
# Bash script to start both backend and frontend for POC Intake

set -e

echo "Starting POC Intake Development Environment..."
echo

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "Checking prerequisites..."

if ! command_exists uv; then
    echo "Error: 'uv' is not installed. Please install uv first."
    echo "Visit: https://github.com/astral-sh/uv"
    exit 1
fi

if ! command_exists npm; then
    echo "Error: 'npm' is not installed. Please install Node.js first."
    echo "Visit: https://nodejs.org/"
    exit 1
fi

# Function to cleanup background processes
cleanup() {
    echo
    echo "Stopping services..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    echo "Services stopped."
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start Backend
echo "Starting Backend (FastAPI)..."
cd backend
uv run python main.py &
BACKEND_PID=$!
cd ..

sleep 2

# Start Frontend
echo "Starting Frontend (Next.js)..."
cd frontend
npx next dev &
FRONTEND_PID=$!
cd ..

sleep 3

# Display status
echo
echo "✅ POC Intake Development Environment Started!"
echo
echo "Services running:"
echo "  - Backend:  http://localhost:8000"
echo "  - Frontend: http://localhost:3000"
echo "  - API Docs: http://localhost:8000/docs"
echo
echo "To test the application:"
echo "  1. Encode an MRN: echo -n 'YOUR_MRN' | base64"
echo "  2. Visit: http://localhost:3000?id=<encoded_mrn>"
echo
echo "Press Ctrl+C to stop all services"

# Wait for processes
wait