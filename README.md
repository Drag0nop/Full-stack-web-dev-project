# Autonomous Codebase Documenter

An MVP web application that ingests a repository ZIP, extracts structure and Python symbols, generates documentation with Gemini when configured, and presents the result in a tree explorer with Q&A and browser voice support.

## What is included

- FastAPI backend with JWT authentication
- ZIP upload and repository parsing
- File tree and metadata generation
- Gemini-backed documentation and Q&A with graceful fallback mode
- Browser-based UI for tree navigation, docs, chat, text-to-speech, and speech-to-text

## Local setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Optionally create a `.env` file in the repo root:

```env
SECRET_KEY=replace-this
GEMINI_API_KEY=your-gemini-key
DATABASE_URL=sqlite:///./documentor.db
MAX_UPLOAD_SIZE_MB=50
```

4. Run the app:

```bash
uvicorn backend.app.main:app --reload
```

5. Open `http://127.0.0.1:8000`.

## API summary

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `GET /api/projects`
- `POST /api/projects/upload`
- `GET /api/projects/{project_id}`
- `POST /api/projects/{project_id}/chat`

## Notes

- Gemini is optional. Without `GEMINI_API_KEY`, the app falls back to heuristic summaries.
- Python files receive AST-based symbol extraction in the current MVP.
- Voice features use browser-native Web Speech APIs for low-friction demo readiness.
