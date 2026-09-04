# Implementation Plan — CheckMyNotes

## Actual Assignment (from recruiter email, received 2026-09-04)

1. Student logs in
2. Uploads handwritten notebook page images, tagged to a subject
3. Pages get checked by **real AI** (free tier — no API key provided, must use your own)
4. Student can view remarks anytime, per subject
5. Downloads: full merged notebook as PDF, or a single day's pages
6. Free tiers rate-limit hard — handle failures gracefully. Accuracy can be rough; **pipeline working end-to-end matters more**.

**Deliverables:** deployed app link, repo access, half-page summary (what's done / what's broken / what's next). Document any assumption made for ambiguous parts.

**Deadline:** Monday midnight (2026-09-07).

---

## What Changed From the Original Plan

The earlier plan treated real AI, PDF export, and login as optional stretch goals. The actual brief makes these **essential**:

- **Real AI checking is required**, not simulated. The simulated evaluator (`ai_service.py`) becomes a *fallback for rate-limit/API failures*, not the primary path.
- **PDF export** (single-day + merged notebook) is a required deliverable, not optional.
- **Login** is required — previously skipped via a hardcoded `DEFAULT_STUDENT_ID`.
- **Deployment** and **GitHub repo access** are new deliverables not in the original plan at all (everything has only run locally so far).
- **A written half-page summary** is a new deliverable.

## 1. What Already Exists (built and tested locally)

- Backend (FastAPI): subjects CRUD, page upload, simulated AI evaluation, notebook retrieval grouped by day, static image serving.
- Frontend (Vite + React): Subject Dashboard, Upload view (auto-triggers evaluation), Notebook Viewer with clickable mistake pins.
- Nothing deployed. No login. No PDF export. No real AI. No remote repo yet.

## 2. What Still Needs to Be Built

- Real AI evaluation call (Groq free-tier vision, matches existing `requirements.txt`) with retry/backoff on 429s, falling back to the simulated evaluator if the AI call keeps failing — so the pipeline never fully breaks.
- Minimal login — simple identity flow, not full password auth (see assumption below).
- PDF export: single-day session PDF, and full merged notebook PDF (`pdf_service.py`, using PyMuPDF already in requirements).
- Push repo to GitHub for reviewer access.
- Deploy backend + frontend somewhere reachable.
- Half-page written summary of status, known issues, and next steps.

## 3. Assumptions to Document in the Final Summary

- **Login** = a lightweight "enter your name" identity step that creates/reuses a student record and stores the student ID in the browser — not full username/password authentication. Chosen for time constraints; noted explicitly as an assumption.
- **AI provider** = Groq free-tier vision model as primary (student's own free API key, read from a `.env` file on the backend — not committed to the repo, no Settings UI built to keep scope tight). Gemini as a second provider only if time allows. Note: the recruiter's tech list mentions "LLaMA 3.3 70B", which is text-only on Groq — this app needs a *vision* model (handwriting images), so we use Groq's vision-capable LLaMA model instead and can speak to general LLaMA-family experience on the call.
- **Rate-limit handling** = on a 429 or AI error, retry a couple of times with backoff; if still failing, fall back to the simulated evaluator and mark the result as such, so upload → check → view never gets stuck.
- **Upload format** = images are the primary supported upload (matches "photos of notebook pages"). Accepting PDF uploads too (converting pages to images via PyMuPDF before AI checking) is a stretch goal, only if essentials finish early.

## 4. Revised Priority for Remaining Time

**Essential (must have for submission)**
1. Real AI evaluation (Groq) wired into the existing `/pages/{id}/evaluate` endpoint, with fallback to simulated evaluator on failure
2. Minimal login (name-based identity, replacing `DEFAULT_STUDENT_ID`)
3. PDF export: single-day PDF, merged notebook PDF — each page rendered with its mistake pins drawn directly onto the image (not just a separate text list), plus the detailed explanation text, so the PDF is self-contained. Simple download buttons in the frontend.
4. Push code to GitHub
5. Deploy backend + frontend (Render, matching the recruiter's tool list)
6. Half-page summary document (`PROJECT_SUMMARY.md`) — what's done, what's broken, what's next, assumptions made

**Nice-to-have if time remains**
- Accept PDF uploads (convert to images via PyMuPDF) alongside image uploads
- Gemini as a second AI provider with auto-switch
- Real password-based auth, multiple students
- Demo data seeder (`seed.py`)
- Polished UI (zoom/pan, animations)

## 5. Recommended Order

1. Real AI service (Groq) + fallback — reuses the existing evaluate endpoint and DB schema, no new tables needed.
2. Minimal login — replaces the hardcoded student ID throughout backend + frontend.
3. PDF export endpoints (with pins drawn on the page images) + frontend download buttons.
4. Push to GitHub.
5. Deploy (Render for backend; Vercel/Netlify or Render static for frontend).
6. Write `PROJECT_SUMMARY.md`.
