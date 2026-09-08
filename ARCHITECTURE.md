# 📓 CheckMyNotes (Acadine) — Complete Project Documentation

> A web app where a student uploads a photo of a handwritten notebook page and a multimodal vision LLM grades it — pinpointing exact mistakes on the image itself, with a deterministic offline fallback so the pipeline never breaks.

---

## 📌 Table of Contents

1. [Project Overview](#-project-overview)
2. [Why This Project Exists](#-why-this-project-exists)
3. [Tech Stack & Why Each Tool Was Chosen](#-tech-stack--why-each-tool-was-chosen)
4. [System Architecture — The Big Picture](#-system-architecture--the-big-picture)
5. [File Structure](#-file-structure)
6. [Complete Request Flow (Endpoint by Endpoint)](#-complete-request-flow-endpoint-by-endpoint)
7. [Every Function Explained](#-every-function-explained)
8. [The Data Layer](#-the-data-layer)
9. [The Frontend Layer](#-the-frontend-layer)
10. [Setup & Installation](#-setup--installation)
11. [Deployment (Render)](#-deployment-render)
12. [Example Input & Output](#-example-input--output)
13. [Design Decisions & Tradeoffs](#-design-decisions--tradeoffs)
14. [Known Limitations](#-known-limitations)
15. [Future Enhancements](#-future-enhancements)

---

## 🧠 Project Overview

CheckMyNotes lets a student:

1. Log in with just a name.
2. Create subjects (Math, Physics, etc.).
3. Upload photos of handwritten notebook pages, tagged to a subject and date.
4. Have each page graded automatically by a vision-capable LLM (Groq's Qwen3.6-27B, configurable via `GROQ_MODEL`).
5. View the grading as **clickable pins directly on the page image** — each pin explains exactly what's wrong (or right) at that spot, with a corrected step and a concept refresher.
6. Download the graded pages as a PDF — a single page, a single day's pages, or the entire subject's notebook merged into one file with pins burned into the image.

The core design goal: **the pipeline must never get stuck**, even with no API key, a bad key, or a rate-limited free tier. Every failure path degrades to a simulated (but deterministic) evaluation instead of erroring out.

---

## 💡 Why This Project Exists

This was built as a timed take-home assignment (3-day deadline) for a recruiter/CEO brief. The brief's actual priorities, in order:

- **Pipeline reliability over grading accuracy.** The brief explicitly says free AI tiers rate-limit hard and "checking accuracy might be rough; ensuring the pipeline works end-to-end matters more."
- **A working, deployed, end-to-end demo** — not a polished production system.
- **Clear reasoning about assumptions and tradeoffs** — the brief asks the candidate to make decisions on ambiguity and document them, and to be ready to explain what was delegated to AI tooling vs. hand-fixed.

Every architectural choice below traces back to those three priorities.

---

## 🛠 Tech Stack & Why Each Tool Was Chosen

| Layer | Tool | Why This and Not Something Else |
|---|---|---|
| **Backend framework** | **FastAPI + Uvicorn** | Async by default (good for I/O-bound AI/file calls), auto-generates OpenAPI docs at `/docs`, minimal boilerplate — fast to build under a deadline. |
| **Data validation** | **Pydantic v2** | The AI's JSON output is untrusted text — Pydantic validates and coerces it into a strict schema (`PageEvaluationResponse`) before it ever reaches the frontend. |
| **Database** | **SQLite + aiosqlite** | Zero setup, file-based, async driver fits FastAPI's async handlers. No need for a separate DB server for a small single-file dataset. |
| **AI vision** | **Groq (Qwen3.6-27B, via an OpenAI-compatible endpoint)** | Groq's free tier is fast and supports vision — needed to read handwriting from a photo, not just text. |
| **Resilience** | **httpx + manual retry loop + simulated fallback** | Groq's free tier returns HTTP 429 often. A retry-with-backoff loop absorbs transient limits; a deterministic offline simulator absorbs everything else so the user is never blocked. |
| **PDF generation** | **PyMuPDF (`fitz`, imported as `pymupdf`)** | Can draw shapes/text directly onto pages and embed images — needed to burn colored mistake pins onto the photo itself, not just list them as text. |
| **Frontend** | **React 18 + Vite** | Fast dev server, simple component model — no need for a heavier framework for a handful of views. |
| **Frontend↔backend link** | **Plain `fetch` in a single `api.js` module** | No axios/React Query needed at this scale — one file of thin wrappers is easier to reason about and modify quickly. |

---

## 🏗 System Architecture — The Big Picture

```
Student (browser)
      │
      │  1. POST /login {name}
      ▼
┌───────────────────────────────┐
│  FastAPI backend (main.py)    │
│  X-Student-Id header = auth   │
└───────────┬────────────────────┘
            │
   2. POST /subjects (create "Math")
   3. POST /pages/upload (files + subject_id + date)
            │
            ▼
┌───────────────────────────────────────────┐
│  Save each file to disk (uploads/)         │
│  SHA-256 hash the image content            │
│  Insert notebook_pages row, status=pending │
└───────────────────┬───────────────────────┘
                    │
       4. POST /pages/{id}/evaluate  (frontend calls this once per uploaded page)
                    │
                    ▼
        ┌───────────────────────────┐
        │ Same image hash seen      │
        │ before (any page)?        │──Yes──► reuse cached evaluation JSON
        └───────────┬───────────────┘
                    │ No
                    ▼
        ┌───────────────────────────┐
        │ GROQ_API_KEY configured?  │──No───► simulate_evaluation(page_id)
        └───────────┬───────────────┘         (deterministic, seeded by page_id)
                    │ Yes
                    ▼
        ┌───────────────────────────┐
        │ call_groq_vision(image)   │
        │ retries: 0,1,3,6s on 429  │──fails──► simulate_evaluation(page_id)
        └───────────┬───────────────┘
                    │ success
                    ▼
        Parse + validate JSON → PageEvaluationResponse
                    │
                    ▼
        Insert evaluations row, mark page "completed"
                    │
                    ▼
      5. GET /subjects/{id}/notebook → grouped by day, with pins
      6. GET .../pdf → PyMuPDF draws pins on the image + a text page
```

**The crucial insight:** the backend never trusts the LLM's output blindly — it's validated against `PageEvaluationResponse` (Pydantic), and every failure mode (no key, bad key, timeout, rate limit, malformed JSON) routes to the same deterministic fallback. The frontend never has to know or care which path produced the result.

---

## 📁 File Structure

```
Acadine/
├── backend/
│   ├── main.py           ← FastAPI routes (login, subjects, upload, evaluate, PDFs)
│   ├── schemas.py        ← Pydantic models for every request/response shape
│   ├── database.py       ← SQLite table definitions + connection dependency
│   ├── ai_service.py     ← Groq vision call, retry logic, simulated fallback
│   ├── pdf_service.py    ← PyMuPDF PDF builder (image pages + text pages)
│   ├── requirements.txt
│   ├── acadine_notebooks.db   ← SQLite file (gitignored)
│   └── uploads/               ← saved page images (gitignored)
├── frontend/
│   ├── src/
│   │   ├── api.js             ← all fetch calls + localStorage student session
│   │   ├── App.jsx            ← header/nav, view switcher, session state
│   │   └── components/
│   │       ├── Login.jsx
│   │       ├── SubjectDashboard.jsx
│   │       ├── UploadView.jsx
│   │       └── NotebookViewer.jsx
│   └── vite.config.js         ← dev-only proxy to localhost:8000
├── render.yaml            ← Render Blueprint: two free-tier services
├── PROJECT_SUMMARY.md      ← half-page deliverable summary (done/broken/next/assumptions)
└── README.md
```

---

## 🔬 Complete Request Flow (Endpoint by Endpoint)

### `POST /login`
Takes just a `name`. Looks up an existing student by exact name match; if found, reuses that student's ID (and therefore all their data). If not found, creates a new student with a generated ID (`stu_<8 hex chars>`). This is the entire auth system — no password.

### `POST /subjects` (requires `X-Student-Id` header)
Creates a subject row scoped to that student. Returns it with `page_count: 0` since it's brand new.

### `GET /subjects`
Lists all subjects for the logged-in student with **live-computed stats**: page count, average score, and last-updated timestamp — computed via a single `LEFT JOIN` + `GROUP BY` query across `subjects → notebook_pages → evaluations`, not stored/cached columns. So stats are always fresh, at the cost of recomputing on every list call (fine at this scale).

### `POST /pages/upload`
Accepts multiple files in one request (`multipart/form-data`) plus `subject_id` and `upload_date`. For each file:
1. Computes the next `page_number` by counting existing pages for that exact (subject, date) pair — so page numbering is per-day, not global.
2. Generates a random `page_id`, saves the file to `uploads/` under a new filename (`{page_id}{original_extension}`), and computes a **SHA-256 hash of the raw bytes**.
3. Inserts a `notebook_pages` row with `status = "pending"`.

Note: **uploading does not evaluate.** It only stores files and creates pending records. The frontend explicitly calls `/evaluate` per page afterward (see UploadView below) — this separation means a slow/failing AI call never blocks the upload response.

### `POST /pages/{page_id}/evaluate`
1. Looks up the page's `image_hash`.
2. **Cache check**: queries for any *other* page with the same hash that already has an evaluation, most recent first. If found, reuses that evaluation's JSON verbatim — no AI call at all.
3. Otherwise calls `evaluate_page()` (see `ai_service.py` below).
4. Inserts a new `evaluations` row and flips the page's status to `"completed"`.

### `GET /subjects/{subject_id}/notebook`
Fetches every page for the subject with its evaluation (if any), then **groups pages into `DailySession` objects keyed by `upload_date`** in Python (not SQL) — SQLite doesn't have Pydantic-shaped nested JSON aggregation, so the grouping happens after fetching rows. Each session gets its own average score and total error count; the subject gets an overall average across all sessions.

### `GET /subjects/{id}/notebook/pdf`, `.../sessions/{date}/pdf`, `/pages/{id}/pdf`
All three share `_fetch_pages_for_pdf()` and `build_notebook_pdf()` — they differ only in which pages get selected (all / one day / one page) before handing off to the same PDF builder.

---

## 🔧 Every Function Explained

### `ai_service.py`

#### `evaluate_page(page_id, image_path) → PageEvaluationResponse`
The single entry point the rest of the app calls. If `GROQ_API_KEY` is set, tries the real vision call; on **any** exception (network error, timeout, malformed response, exhausted retries), it logs the failure and falls through to `simulate_evaluation()` — it never lets an exception propagate up to the API layer.

#### `call_groq_vision(image_path) → PageEvaluationResponse`
Base64-encodes the image into a `data:image/...;base64,...` URL and sends it as a multimodal chat message alongside a text prompt (`EVALUATION_PROMPT`) that demands a strict JSON shape back. Retries on HTTP 429 using `RETRY_DELAYS = [0, 1, 3, 6]` seconds — a short exponential-ish backoff tuned for Groq's per-minute token limit. `temperature=0.2` keeps grading fairly consistent without being fully rigid.

#### `_parse_evaluation_json(content) → PageEvaluationResponse`
LLMs often wrap JSON in prose or markdown fences even when told not to. This finds the first `{` and last `}` in the response and slices out everything between them before `json.loads`, then fills in `total_mistakes`/`total_warnings` by counting severities if the model omitted them, then validates the whole thing against the Pydantic schema — so a malformed or incomplete response raises here and gets caught by `evaluate_page`'s fallback.

#### `simulate_evaluation(page_id) → PageEvaluationResponse`
Used whenever there's no API key or the real call fails. Seeds Python's `random.Random` **with the `page_id` itself**, so the same page always produces the same simulated score, grade, and pins — the "fake" result is stable and repeatable, not different every refresh. Picks 1–3 remarks from a fixed `SAMPLE_REMARKS` pool and scatters them at random (but seeded) coordinates.

### `pdf_service.py`

#### `_add_image_page(doc, image_path, evaluation)`
Adds a new PDF page sized to A4, places the notebook photo inside the margins, then for every mistake pin draws a filled circle (colored red/orange/green by severity) at the pin's `(x_percent, y_percent)` position — converting percentages into absolute point coordinates relative to the image's placement rectangle — with the pin's index number drawn in white on top.

#### `_add_evaluation_page(...)`
Adds a plain-text page: subject/page/date header, score + grade label, the summary, then every mistake numbered with its title, explanation, correction, and concept tip — using `_wrap_and_insert` to manually word-wrap text to the page width (PyMuPDF has no built-in paragraph flow, so wrapping is measured word-by-word with `pymupdf.get_text_length`). If content overflows the page height mid-loop, it starts a fresh page.

#### `build_notebook_pdf(subject_name, pages) → bytes`
For every page in the list, emits one image page immediately followed by one evaluation page — so the PDF is self-contained and readable standalone (photo + full explanation, in order), without needing the live app.

### `main.py` — helper functions

#### `_fetch_pages_for_pdf(db, subject_id, upload_date=None)`
Shared query used by all three PDF endpoints; `upload_date` is optional so the same function serves both "one day" and "whole subject" requests by just adding or omitting a `WHERE` clause.

#### `_get_owned_subject_name(db, subject_id, student_id)`
Enforces that a student can only generate a PDF for a subject **they own** — the only per-request ownership check in the codebase beyond the header-based student_id filter already baked into most queries.

---

## 📊 The Data Layer

### Tables (`database.py`)

| Table | Key columns | Purpose |
|---|---|---|
| `students` | `id`, `name` | Created/reused on login |
| `subjects` | `id`, `student_id`, `name`, `color` | Owned by a student |
| `notebook_pages` | `id`, `subject_id`, `upload_date`, `page_number`, `file_path`, `status`, `image_hash` | One row per uploaded image |
| `evaluations` | `id`, `page_id` (UNIQUE), `score`, `raw_json` | One row per evaluated page; `raw_json` stores the full `PageEvaluationResponse` for exact re-serialization |

`page_id` is `UNIQUE` on `evaluations`, so a page can only ever have one evaluation row — re-evaluating would need a different design (currently there's no "re-check" endpoint, so this hasn't come up).

### `schemas.py` — the contract between AI output and the frontend

`PageEvaluationResponse` and its nested `MistakePin` are the most important models in the app: they're what the AI's raw JSON gets validated against, and exactly what the frontend renders. `MistakePin.severity` is a `Literal["error", "warning", "good"]` — this is what drives both the pin color on the image and the CSS class in React (`pin-error`, `pin-warning`, `pin-good`).

---

## 🖥 The Frontend Layer

### `api.js` — the only place that talks to the backend
- `API_BASE` reads `import.meta.env.VITE_API_URL`, defaulting to `''` (relative paths). In local dev this is empty, so requests hit Vite's dev proxy; in production it's set to the deployed backend's URL so the static frontend can reach a backend on a different domain.
- `authHeaders()` reads the stored student from `localStorage` and attaches `X-Student-Id` — this header **is** the auth system from the frontend's side.
- `triggerDownload(blob, filename)` is a small trick to force a browser download from a `fetch` response: create an object URL, synthesize an `<a download>`, click it programmatically, then revoke the URL.

### `App.jsx`
Holds the logged-in student in state (initialized from `localStorage` so refreshing the page doesn't log you out) and a simple `view` string (`'dashboard' | 'upload' | 'notebook'`) that swaps which component renders — no router library, just conditional rendering.

### `UploadView.jsx`
After `uploadPages()` returns the list of newly created pages, it **awaits `evaluatePage()` in a sequential `for` loop**, one page at a time, rather than firing them all concurrently with `Promise.all`. This is deliberate: Groq's free tier caps output tokens per minute, so sending one page's images at a time (rather than bursting several vision calls simultaneously) reduces how quickly a multi-page upload burns through the per-minute quota.

### `NotebookViewer.jsx`
Fetches a subject's full notebook, renders each day as a card with page buttons, and for the selected page overlays absolutely-positioned `<span>` pins on top of the `<img>` using the same `x_percent`/`y_percent` the PDF uses — so the on-screen view and the downloaded PDF show mistakes in the exact same spots, from the same data. Clicking a pin just sets `activeMistake` in state to show its detail popup; no extra network call is needed since the whole evaluation was already fetched with the notebook.

---

## ⚙️ Setup & Installation

```bash
# Backend
cd backend
python -m venv venv && .\venv\Scripts\activate   # Windows
pip install -r requirements.txt
# create backend/.env with: GROQ_API_KEY=your_key_here   (optional — omit to run fully on the simulated fallback)
uvicorn main:app --reload

# Frontend
cd frontend
npm install
npm run dev   # proxies /login, /subjects, /pages, /uploads to localhost:8000
```

---

## ☁️ Deployment (Render)

Deployed as two services from one `render.yaml` Blueprint:

- **`acadine-backend`** — Python web service (`plan: free` explicitly set — Render defaults to a paid plan if `plan` is omitted). Env vars: `GROQ_API_KEY`, `FRONTEND_URL` (used for CORS `allow_origins`).
- **`acadine-frontend`** — static site (`runtime: static`, built with `npm run build`). Static sites have no `plan` field at all — they're always free. Env var: `VITE_API_URL`, pointing at the backend's URL.

Because the two services land on different domains, `main.py` adds `CORSMiddleware` restricted to `FRONTEND_URL`, and `api.js`/`NotebookViewer.jsx` prefix every request/image URL with `API_BASE` instead of the relative paths the Vite dev proxy used locally.

**Caveat worth stating out loud in an interview:** Render's free web services have **ephemeral disk** — the SQLite file and `uploads/` directory reset whenever the backend service restarts or redeploys. Fine for a graded demo, not for real persistence (would need a managed Postgres + object storage like S3 for that).

---

## 📥 Example Input & Output

**Request:** `POST /pages/{page_id}/evaluate`

**AI's raw response (before parsing):**
```json
{
  "score": 8.0,
  "grade_label": "B - Good Effort",
  "summary": "Correct method overall, one sign error near the end.",
  "mistakes": [
    {
      "id": "pin-1",
      "x_percent": 42.0,
      "y_percent": 61.0,
      "severity": "error",
      "title": "Sign error in step 3",
      "explanation": "The negative sign was dropped when moving -2x across the equals sign.",
      "corrected_step": "-2x = -8  ->  x = 4",
      "concept_refresher": "Moving a term to the other side flips its sign."
    }
  ],
  "key_concepts_tested": ["Linear equations"],
  "strengths": ["Clear working shown"],
  "areas_to_improve": ["Double-check signs when moving terms"]
}
```
This gets validated into `PageEvaluationResponse`, stored as `raw_json` in `evaluations`, and rendered as a red pin at 42%/61% on the image both in the browser and in the exported PDF.

---

## 🤔 Design Decisions & Tradeoffs

| Decision | Alternative Considered | Why This Choice Won |
|---|---|---|
| Name-only login via `X-Student-Id` header | Full username/password + JWT | Brief prioritized a working end-to-end pipeline over auth depth, given the 3-day deadline |
| Cache evaluations by image SHA-256 hash | No caching / re-call AI every time | Groq's free tier is tightly rate-limited; identical images (re-uploads, retries) shouldn't burn quota or produce different scores each time |
| Sequential `evaluate` calls after upload (not parallel) | `Promise.all` on all pages | Reduces the chance of bursting past Groq's per-minute output-token cap on multi-page uploads |
| Deterministic fallback seeded by `page_id` | Fully random fallback | The brief explicitly values pipeline reliability; a stable "fake" result is more trustworthy for demoing than a different one every retry |
| Upload and evaluate as two separate endpoints | One combined upload-and-grade endpoint | A slow/failing AI call never blocks the (fast) file upload; the frontend can show "uploaded" immediately and "evaluating" separately |
| PyMuPDF drawing pins directly onto the photo | Store mistake coordinates only, render pins client-side only | The brief asks for exportable PDFs; pins had to be reproducible outside the browser, so they're burned into the image at export time using the same percentage coordinates the UI uses |
| SQLite | Postgres/MySQL | No server to provision; the whole app is a single small demo dataset |

---

## ⚠️ Known Limitations

- No password auth — anyone entering an existing student's exact name reuses that student's data.
- The evaluation cache is **global by image hash**, not scoped per student — two different students uploading byte-identical images would share a cached result (very unlikely in practice, but not impossible).
- Only image uploads (JPG/PNG); no PDF-file upload support.
- Render free-tier deploy has no persistent disk — data resets on backend restart/redeploy.

---

## 🌟 Future Enhancements

- Real authentication (passwords or OAuth) instead of name-only login.
- Scope the evaluation cache per-student and add a DB index on `image_hash`.
- Support PDF-file uploads (convert pages to images server-side before grading).
- Swap SQLite + local disk for Postgres + object storage to survive redeploys.

---

*Built with FastAPI · Pydantic v2 · SQLite/aiosqlite · Groq (Qwen3.6-27B) · PyMuPDF · React 18 + Vite · deployed on Render.*
