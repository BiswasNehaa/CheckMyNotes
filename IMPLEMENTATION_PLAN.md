# Implementation Plan — Acadine (3-Day MVP)

## Assignment Goal

Build a web app where students can:
1. Access a student profile
2. Upload handwritten notebook page images tagged by subject
3. Send pages to an AI vision model for evaluation
4. View AI remarks organized by subject and date
5. Download a single day's pages or a merged notebook as PDF

Keep it simple. Build and test one feature at a time. Do not start the next feature until the current one works.

---

## 1. What Already Exists

- `backend/database.py` — SQLite tables ready: `students`, `subjects`, `notebook_pages`, `evaluations`, `settings`. Async `get_db()` dependency + `init_db()`.
- `backend/schemas.py` — Pydantic v2 models ready: `MistakePin`, `PageEvaluationResponse`, `SubjectCreate/Response`, `PageItem`, `DailySession`, `NotebookResponse`, `ApiKeyConfigRequest`.
- `backend/requirements.txt` — correct deps already listed (fastapi, aiosqlite, pymupdf, pillow, httpx, etc).
- `backend/uploads/` folder ready for saved images.
- Nothing else yet: no `main.py`, no AI service, no PDF service, no frontend.

## 2. What Still Needs to Be Built

**Backend**
- `main.py` — FastAPI app: student & subject endpoints, upload endpoint, notebook/list endpoints.
- `ai_service.py` — analyzes an uploaded image, returns a `PageEvaluationResponse` (score, remarks, mistake pins). Graceful failure handling if the AI call fails/rate-limits.
- Wire upload → save file → run AI service → store evaluation in DB.

**Frontend**
- New Vite + React app.
- Minimal pages: subject list, upload form, notebook viewer showing image + remarks/pins, previous uploads browse.

**Optional/stretch**
- `pdf_service.py` (single-day PDF, merged notebook PDF)
- Real Groq/Gemini API integration with retry/backoff
- Multiple student profiles, settings page, zoom/pan/polished UI

## 3. Recommended Implementation Order

One feature at a time, each tested before moving on:

1. **Backend skeleton** — `main.py` with `init_db()` wired in, health check route, students/subjects CRUD. Test via `/docs`.
2. **Upload endpoint** — accept image file(s), save to `uploads/`, assign subject + date, create `notebook_pages` row (status `pending`).
3. **AI evaluation** — start with a simple offline/simulated evaluator (no API key needed, always works) so the pipeline is reliable; store result in `evaluations` table, mark page `completed`. Add real AI provider call afterward if time allows, with fallback to simulated on failure.
4. **Notebook/list endpoints** — return `NotebookResponse`/`DailySession` so the frontend has something to render; supports browsing previous uploads by subject/date.
5. **Frontend: subject list + upload form** — basic React pages hitting the backend.
6. **Frontend: notebook viewer** — show image + AI remarks/pins from the evaluation.
7. *(If time remains)* Real Groq/Gemini API call in `ai_service.py` with graceful error handling and retry.
8. *(If time remains)* PDF export endpoint (single day, then merged notebook).

## 4. Priority: Essential vs Optional

**Essential (MVP, must work end-to-end)**
- Backend CRUD for subjects + upload
- AI evaluation (simulated evaluator is acceptable) with basic failure handling
- Notebook/remarks viewing by subject and date
- Frontend: upload a page, browse subjects, see the graded result

**Optional (only if Days 1-2 finish early)**
- Real Groq/Gemini AI integration with retry/backoff
- PDF export (single day / merged notebook)
- Multiple student profiles, settings UI for API keys
- Polished UI (zoom/pan canvas, pulsating pins, animations)
