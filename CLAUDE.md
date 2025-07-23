# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Important: WSL and Google Cloud Authentication

When running through WSL, gcloud commands cannot be authenticated directly. For any gcloud commands:
1. Either create a script that the user can run
2. Or provide the exact commands as a single line (for Windows Terminal compatibility)
3. The user will execute these commands and report back the results

Always format gcloud commands as single-line for easy copy/paste in Windows Terminal.

## Development Commands

### Backend (Python/FastAPI)
```bash
# Run the FastAPI server locally
uvicorn app.main:app --reload

# Alternative using main.py entry point
python main.py

# Run with specific host/port
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend (Node.js)
```bash
# Install frontend dependencies
cd frontend && npm install

# Run development server
npm run dev

# Build for production
npm run build

# Run production build
npm start
```

### Testing
```bash
# Backend tests using pytest
pytest

# Run specific test file
pytest tests/test_api.py

# Run with coverage
pytest --cov=app

# Frontend tests
cd frontend && npm test

# Run frontend tests in watch mode
cd frontend && npm run test:watch
```

### Dependencies
```bash
# Backend: Install with pip
pip install -r requirements.txt

# Backend: Install with uv (if using uv)
uv sync

# Frontend: Install with npm
cd frontend && npm install
```

## Architecture Overview

This is a full-stack application with:
- **Backend**: FastAPI (Python) REST API
- **Frontend**: Node.js/JavaScript web application

### Backend Structure
```
app/
├── main.py              # FastAPI application entry point
├── core/                # Core infrastructure
│   ├── config.py        # Configuration management
│   ├── auth.py          # Authentication logic
│   └── database.py      # Database connections
├── models/              # Data models/schemas
├── routers/             # API endpoints
├── services/            # Business logic
├── repositories/        # Data access layer
└── utils/               # Utility functions

tests/                   # Backend tests
requirements.txt         # Python dependencies
```

### Frontend Structure
```
frontend/
├── src/
│   ├── components/      # React/Vue components
│   ├── pages/           # Page components
│   ├── services/        # API client services
│   ├── utils/           # Frontend utilities
│   └── index.js         # Entry point
├── public/              # Static assets
├── package.json         # Node dependencies
└── webpack.config.js    # Build configuration
```

### Data Flow
Frontend → API Request → Router → Service → Repository → Database

## Technology Stack

### Backend
- **Framework**: FastAPI with uvicorn
- **Database**: PostgreSQL/SQLite (configure as needed)
- **ORM**: SQLAlchemy (if using)
- **Authentication**: JWT tokens
- **Testing**: pytest
- **API Documentation**: Auto-generated at `/docs`

### Frontend
- **Framework**: React/Vue/Vanilla JS (configure as needed)
- **Build Tool**: Webpack/Vite
- **HTTP Client**: Axios/Fetch API
- **Testing**: Jest/Vitest

## Key Integration Points

### API Communication
- Backend runs on `http://localhost:8000`
- Frontend runs on `http://localhost:3000`
- CORS configured in FastAPI for frontend access
- API endpoints follow RESTful conventions

### Charm Tracker API Integration
- **API Documentation**: The `api_docs/` folder contains JSON files with detailed specifications for all Charm Tracker API endpoints
- **Important**: Always consult the appropriate API documentation file when creating or editing Charm API calls to ensure correct payload structure, field names, and data types
- Example API docs include:
  - `Allergy API.json` - For patient allergy management
  - `Patient API.json` - For patient demographics
  - `Medication API.json` - For patient medications
  - `Medical History API.json` - For medical history data
- Each API doc specifies required fields, optional fields, valid enum values, and expected response formats
- **Best Practice**: Before implementing any Charm API integration, review the corresponding JSON file in `api_docs/` to understand the exact payload requirements

### Authentication Flow
1. Frontend sends credentials to `/auth/login`
2. Backend validates and returns JWT token
3. Frontend stores token and includes in API requests
4. Backend validates token on protected endpoints

## Development Guidelines

### Backend Development

#### Adding New API Endpoints
1. Create router file in `app/routers/`
2. Define endpoint functions with proper typing
3. Create corresponding service in `app/services/`
4. Register router in `app/main.py`
5. Add tests in `tests/`

#### API Endpoint Pattern
```python
from fastapi import APIRouter, Depends, HTTPException
from app.core.auth import get_current_user

router = APIRouter(prefix="/api/v1/resource", tags=["resource"])

@router.get("/{id}")
async def get_resource(id: int, current_user=Depends(get_current_user)):
    # Implementation
```

### Frontend Development

#### API Service Pattern
```javascript
// frontend/src/services/api.js
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const apiClient = {
  get: async (endpoint) => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: {
        'Authorization': `Bearer ${getToken()}`
      }
    });
    return response.json();
  }
};
```

### Environment Configuration
- Backend: Environment variables in `.env` file
- Frontend: Environment variables in `.env.local` or build config
- Never commit sensitive credentials

## Common Tasks

### Running Full Stack Locally
```bash
# Terminal 1: Start backend
uvicorn app.main:app --reload

# Terminal 2: Start frontend
cd frontend && npm run dev
```

### Adding New Feature
1. Design API endpoint in backend
2. Implement backend logic with tests
3. Create frontend components
4. Connect frontend to backend API
5. Test full integration

### Database Operations
- Migrations handled via Alembic (if using)
- Direct SQL queries in repositories
- Use async database operations

### CORS Configuration
Ensure FastAPI CORS middleware is configured for frontend origin:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Development Rules

### Field Management
- NEVER hardcode field names, field mappings, or field lists
- ALWAYS derive field information from Pydantic models
- This ensures a single source of truth for all field definitions
- Any hardcoding of fields must be explicitly approved by the user