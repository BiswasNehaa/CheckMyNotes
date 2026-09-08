# 📚 AI Student Notebook Checker

An AI-powered academic web application where students upload photos of their handwritten notebook pages, have them automatically evaluated by a multimodal AI vision model (Groq's Qwen3.6-27B), review pinpointed visual mistake annotations per subject, and export single-day or merged semester notebook PDFs.

---

## 🚀 Key Features

1. **Student Dashboard & Profile**: Switch student profiles, track subjects, and monitor average grades.
2. **Daily Multi-Page Upload**: Drag-and-drop handwritten scans/photos, tag to a subject (Math, Physics, Chemistry, etc.), set upload dates, and preview pages.
3. **AI Vision Checking Pipeline**:
   - Uses **Groq (Qwen3.6-27B vision, configurable via `GROQ_MODEL`)** on the free tier.
   - Generates scores, teacher remarks, step-by-step green/red correctness checks, and normalized `(X, Y)` coordinate pins.
   - **Rate-Limit Resilience**: Exponential backoff retry handler for HTTP 429 errors.
   - **Honest Failure Handling**: if the AI is unavailable after retries, the page is marked `failed` with a clear retry option — never a fabricated grade.
4. **Interactive Notebook & Remarks Viewer**:
   - Per-subject digital binder with daily session timeline filters.
   - Zoomable page canvas with interactive pulsating error pins.
   - Side-by-side critique panel with step explanations, corrected formulas, and concept refresher tips.
5. **PyMuPDF PDF Export Engine**:
   - **Single-Day Session PDF**: That day's annotated scans + grading sheet.
   - **Full Merged Notebook PDF**: Complete subject archive with Cover Page, Table of Contents, and chronological notes.

---

## 🛠️ Technology Stack & Architecture

| Layer | Technologies | Purpose |
| :--- | :--- | :--- |
| **Backend API** | **Python 3.13 + FastAPI + Uvicorn** | High-performance asynchronous REST API with auto-generated interactive OpenAPI docs (`/docs`). |
| **Data Validation** | **Pydantic v2** | Strict, type-safe schemas for AI vision outputs, error coordinates, and upload payloads. |
| **AI / Vision Pipeline** | **Groq API (Qwen3.6-27B vision)** | Multimodal handwriting OCR & step-by-step grading on free tier, with prompt engineering. |
| **Resilience** | **httpx + manual retry loop** | Handles rate-limiting (HTTP 429) with exponential backoff retries; a failure that survives retries is reported explicitly, never masked. |
| **PDF Generation** | **PyMuPDF (`fitz`)** | Fast, high-fidelity PDF compilation with table of contents, annotated scans, and summary cards. |
| **Database** | **SQLite + aiosqlite** | Lightweight, file-based persistent storage for subjects, daily uploads, and AI remarks. |
| **Frontend UI** | **React 18 + Vite + Modern CSS** | Interactive notebook canvas with zoom/pan, pulsating mistake pins, timeline filter, and student dashboard. |
| **UI Icons** | **Lucide React** | Clean, modern iconography for student tools. |

---

## 📁 Project Structure

```
Acadine/
├── backend/
│   ├── main.py          # FastAPI REST endpoints & background tasks
│   ├── schemas.py       # Pydantic v2 data models
│   ├── database.py      # SQLite tables & async connection manager
│   ├── ai_service.py    # AI vision pipeline & retry logic
│   ├── pdf_service.py   # PyMuPDF PDF compilation engine
│   ├── seed.py          # Sample notebook data generator
│   └── requirements.txt # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/  # UploadCenter, NotebookViewer, RemarksPanel, etc.
│   │   ├── App.jsx      # Main application router & state
│   │   └── index.css    # Custom notebook design tokens
│   ├── package.json     # Frontend dependencies
│   └── vite.config.js
└── IMPLEMENTATION_PLAN.md
```

---

## 🚀 Self-Hosting

This project runs on one shared AI backend, so if you fork/clone it, you'll need your own free API key — it takes 2 minutes:

1. **Get a free Groq API key** at [console.groq.com](https://console.groq.com) (no credit card needed).
2. **Backend setup:**
   ```bash
   cd backend
   python -m venv venv && venv\Scripts\activate   # Windows; use `source venv/bin/activate` on Mac/Linux
   pip install -r requirements.txt
   ```
   Create a `backend/.env` file with:
   ```
   GROQ_API_KEY=your_key_here
   ```
   Then run it:
   ```bash
   uvicorn main:app --reload
   ```
3. **Frontend setup:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

No key? Uploading still works, but evaluation will return "AI unavailable" for every page — a Groq API key is required to actually grade anything.

---

For a deep dive into the architecture, request flow, and every function, see [ARCHITECTURE.md](./ARCHITECTURE.md).
