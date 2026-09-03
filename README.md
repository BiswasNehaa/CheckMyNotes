# 📚 AI Student Notebook Checker

An AI-powered academic web application where students upload photos of their handwritten notebook pages, have them automatically evaluated by multimodal AI vision models (Groq LLaMA 3.2 Vision & Gemini 1.5 Flash), review pinpointed visual mistake annotations per subject, and export single-day or merged semester notebook PDFs.

---

## 🚀 Key Features

1. **Student Dashboard & Profile**: Switch student profiles, track subjects, and monitor average grades.
2. **Daily Multi-Page Upload**: Drag-and-drop handwritten scans/photos, tag to a subject (Math, Physics, Chemistry, etc.), set upload dates, and preview pages.
3. **AI Vision Checking Pipeline**:
   - Uses **Groq (LLaMA 3.2 11B/90B Vision)** & **Google Gemini 1.5 Flash** on free tiers.
   - Generates scores, teacher remarks, step-by-step green/red correctness checks, and normalized `(X, Y)` coordinate pins.
   - **Rate-Limit Resilience**: Exponential backoff retry handler for HTTP 429 errors.
   - **Smart Fallback Engine**: Built-in offline evaluation simulation guaranteeing 100% demo uptime without requiring an API key.
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
| **AI / Vision Pipeline** | **Groq API (LLaMA 3.2 Vision) & Google Gemini 1.5 Flash** | Multimodal handwriting OCR & step-by-step grading on free tier, with prompt engineering. |
| **Resilience & Fallback** | **Python Backoff + Smart Offline Evaluator** | Handles rate-limiting (HTTP 429) smoothly with exponential retries and built-in offline simulation if no API key is provided. |
| **PDF Generation** | **PyMuPDF (`fitz`) + Pillow (PIL)** | Fast, high-fidelity PDF compilation with table of contents, annotated scans, and summary cards. |
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
│   ├── ai_service.py    # AI vision pipeline, retries & smart fallback
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
