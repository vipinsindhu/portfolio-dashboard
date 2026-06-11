# Portfolio Dashboard — Project Conventions

## Testing (required)

- **Every code change must keep the test suite green.** Run `python -m pytest backend/tests -q` before committing.
- **Every new feature or behavior change must include test updates** in the same commit:
  - New/changed backend logic → unit tests in `backend/tests/`
  - New/changed API endpoints → endpoint tests in `backend/tests/test_api.py`
  - New user-facing flows → consider extending `tests/e2e/smoke.js`
- CI (`.github/workflows/ci.yml`) runs backend tests, the frontend build, and a Playwright smoke test on every push to `main`.

## Deployment

- Hosting: Railway, auto-deploys on push to `main`. Live at https://portfolio-builder.up.railway.app/
- The Flask backend serves the **committed** `frontend/dist/` directly. Frontend changes require:
  1. `cd frontend && npx vite build`
  2. Commit the updated `frontend/dist/` along with the source changes
- The demo flow ("Try a Demo" button) uploads a sample portfolio via `/api/portfolio/upload`, which **replaces** the stored portfolio. Tests in `backend/tests/test_api.py` pin this behavior — keep them updated if the demo portfolio changes.

## Architecture notes

- Backend modules use flat imports (`from portfolio import ...`); `backend/` is added to `sys.path`. Tests handle this in `backend/tests/conftest.py`.
- Backend reads/writes data files (portfolio.json, sector_cache.json) relative to the working directory. Tests run in a temp directory for isolation.
- LLM calls go through Groq (`backend/signals.py`). There is no Anthropic integration.

## Security

- Never commit API keys, registry credentials, or other secrets — use environment variables (Railway dashboard) and GitHub Actions secrets.
