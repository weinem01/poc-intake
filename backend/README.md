# POC Intake Backend

Patient intake system backend for Pound of Cure Weight Loss.

## Setup with UV

1. **Install UV** (if not already installed):
   ```bash
   # On Windows (PowerShell)
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   
   # On macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Set up the project**:
   ```bash
   # Navigate to backend directory
   cd backend
   
   # Create virtual environment and install dependencies
   uv venv
   uv sync
   ```

3. **Activate the virtual environment**:
   ```bash
   # On Windows (PowerShell)
   .venv\Scripts\activate
   
   # On macOS/Linux
   source .venv/bin/activate
   ```

4. **Set up Google Cloud authentication**:
   ```bash
   # Make sure you're authenticated with gcloud
   gcloud auth application-default login
   ```

5. **Run the application**:
   ```bash
   # With UV (recommended)
   uv run python main.py
   
   # Or if virtual environment is activated
   python main.py
   
   # Or using uvicorn directly
   uv run uvicorn app.main:app --reload
   ```

## Alternative: Using UV without activation

You can run commands directly through UV without activating the virtual environment:

```bash
# Install dependencies
uv sync

# Run the application
uv run python main.py

# Run with uvicorn
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Development

### Running tests
```bash
uv run pytest
```

### Adding new dependencies
```bash
# Add to pyproject.toml then run:
uv sync
```

## Environment Variables

The application uses Google Secret Manager for sensitive data. Ensure you're authenticated with the correct GCP project:

- Development: `pound-of-cure-dev`
- Production: `pound-of-cure-llc`

The application automatically detects the environment based on deployment context.