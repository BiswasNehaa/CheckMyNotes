import hashlib
import uuid
from datetime import datetime
from pathlib import Path
from typing import List

import aiofiles
import aiosqlite
from fastapi import FastAPI, Depends, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

from ai_service import evaluate_page
from database import init_db, get_db, UPLOADS_DIR
from pdf_service import build_notebook_pdf
from schemas import (
    DailySession,
    LoginRequest,
    NotebookResponse,
    PageEvaluationResponse,
    PageItem,
    StudentResponse,
    SubjectCreate,
    SubjectResponse,
)

app = FastAPI(title="Acadine API")


async def get_student_id(x_student_id: str = Header(..., alias="X-Student-Id")) -> str:
    """Identify the logged-in student from a request header (set after /login)."""
    return x_student_id

# Serve uploaded page images so the frontend can display them.
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")


@app.on_event("startup")
async def on_startup():
    """Create database tables (if they don't exist yet) when the server starts."""
    await init_db()


@app.get("/health")
async def health():
    """Simple check to confirm the backend is running."""
    return {"status": "ok"}


@app.post("/login", response_model=StudentResponse)
async def login(payload: LoginRequest, db: aiosqlite.Connection = Depends(get_db)):
    """Log in with just a name: reuses the existing student record, or creates one."""
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Name is required")

    cursor = await db.execute("SELECT id, name FROM students WHERE name = ?", (name,))
    row = await cursor.fetchone()
    if row:
        return StudentResponse(id=row["id"], name=row["name"])

    student_id = f"stu_{uuid.uuid4().hex[:8]}"
    await db.execute(
        "INSERT INTO students (id, name, grade) VALUES (?, ?, ?)",
        (student_id, name, ""),
    )
    await db.commit()
    return StudentResponse(id=student_id, name=name)


@app.post("/subjects", response_model=SubjectResponse)
async def create_subject(
    subject: SubjectCreate,
    db: aiosqlite.Connection = Depends(get_db),
    student_id: str = Depends(get_student_id),
):
    """Create a new subject (e.g. Mathematics) for the logged-in student."""
    subject_id = f"sub_{uuid.uuid4().hex[:8]}"
    await db.execute(
        "INSERT INTO subjects (id, student_id, name, color, description) VALUES (?, ?, ?, ?, ?)",
        (subject_id, student_id, subject.name, subject.color, subject.description),
    )
    await db.commit()

    return SubjectResponse(
        id=subject_id,
        name=subject.name,
        color=subject.color,
        description=subject.description,
        page_count=0,
        average_score=None,
        last_updated=None,
    )


@app.get("/subjects", response_model=List[SubjectResponse])
async def list_subjects(
    db: aiosqlite.Connection = Depends(get_db),
    student_id: str = Depends(get_student_id),
):
    """List all subjects for the logged-in student, with actual page counts and average scores."""
    cursor = await db.execute(
        """SELECT s.id, s.name, s.color, s.description,
                  COUNT(p.id) AS page_count,
                  AVG(e.score) AS average_score,
                  MAX(p.created_at) AS last_updated
           FROM subjects s
           LEFT JOIN notebook_pages p ON p.subject_id = s.id
           LEFT JOIN evaluations e ON e.page_id = p.id
           WHERE s.student_id = ?
           GROUP BY s.id""",
        (student_id,),
    )
    rows = await cursor.fetchall()

    return [
        SubjectResponse(
            id=row["id"],
            name=row["name"],
            color=row["color"],
            description=row["description"],
            page_count=row["page_count"],
            average_score=round(row["average_score"], 1) if row["average_score"] is not None else None,
            last_updated=row["last_updated"],
        )
        for row in rows
    ]


@app.post("/pages/upload")
async def upload_pages(
    subject_id: str = Form(...),
    upload_date: str = Form(...),
    files: List[UploadFile] = File(...),
    db: aiosqlite.Connection = Depends(get_db),
    student_id: str = Depends(get_student_id),
):
    """Save uploaded notebook page images and create a 'pending' record for each."""
    uploaded = []

    count_cursor = await db.execute(
        "SELECT COUNT(*) AS count FROM notebook_pages WHERE subject_id = ? AND upload_date = ?",
        (subject_id, upload_date),
    )
    count_row = await count_cursor.fetchone()
    next_page_number = count_row["count"] + 1

    for offset, file in enumerate(files):
        index = next_page_number + offset
        page_id = f"page_{uuid.uuid4().hex[:8]}"
        file_name = f"{page_id}{Path(file.filename).suffix}"

        contents = await file.read()
        image_hash = hashlib.sha256(contents).hexdigest()
        async with aiofiles.open(UPLOADS_DIR / file_name, "wb") as out_file:
            await out_file.write(contents)

        await db.execute(
            """INSERT INTO notebook_pages
               (id, student_id, subject_id, upload_date, page_number, file_path, status, image_hash)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (page_id, student_id, subject_id, upload_date, index, file_name, "pending", image_hash),
        )

        uploaded.append({
            "id": page_id,
            "subject_id": subject_id,
            "upload_date": upload_date,
            "page_number": index,
            "image_url": f"/uploads/{file_name}",
            "status": "pending",
        })

    await db.commit()
    return {"uploaded": uploaded}


@app.post("/pages/{page_id}/evaluate", response_model=PageEvaluationResponse)
async def evaluate_uploaded_page(page_id: str, db: aiosqlite.Connection = Depends(get_db)):
    """Run AI evaluation on a single uploaded page and store the result."""
    cursor = await db.execute(
        "SELECT id, file_path, image_hash FROM notebook_pages WHERE id = ?", (page_id,)
    )
    page = await cursor.fetchone()
    if page is None:
        raise HTTPException(status_code=404, detail="Page not found")

    # Reuse a prior evaluation if this exact image was already checked, so identical
    # pages give identical results and we don't burn the AI's tiny free-tier quota twice.
    cached_evaluation = None
    if page["image_hash"]:
        cache_cursor = await db.execute(
            """SELECT e.raw_json FROM notebook_pages p
               JOIN evaluations e ON e.page_id = p.id
               WHERE p.image_hash = ? AND p.id != ?
               ORDER BY e.created_at DESC LIMIT 1""",
            (page["image_hash"], page_id),
        )
        cache_row = await cache_cursor.fetchone()
        if cache_row:
            cached_evaluation = PageEvaluationResponse.model_validate_json(cache_row["raw_json"])

    evaluation = cached_evaluation or await evaluate_page(page_id, UPLOADS_DIR / page["file_path"])

    await db.execute(
        """INSERT INTO evaluations
           (id, page_id, score, grade_label, summary, total_mistakes, total_warnings, raw_json)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            f"eval_{uuid.uuid4().hex[:8]}",
            page_id,
            evaluation.score,
            evaluation.grade_label,
            evaluation.summary,
            evaluation.total_mistakes,
            evaluation.total_warnings,
            evaluation.model_dump_json(),
        ),
    )
    await db.execute("UPDATE notebook_pages SET status = 'completed' WHERE id = ?", (page_id,))
    await db.commit()

    return evaluation


@app.get("/subjects/{subject_id}/notebook", response_model=NotebookResponse)
async def get_subject_notebook(
    subject_id: str,
    db: aiosqlite.Connection = Depends(get_db),
    student_id: str = Depends(get_student_id),
):
    """Return all uploaded pages (with evaluations, if any) for a subject, grouped by day."""
    subject_cursor = await db.execute(
        "SELECT id, name, color, description FROM subjects WHERE id = ? AND student_id = ?",
        (subject_id, student_id),
    )
    subject_row = await subject_cursor.fetchone()
    if subject_row is None:
        raise HTTPException(status_code=404, detail="Subject not found")

    pages_cursor = await db.execute(
        """SELECT p.id, p.upload_date, p.page_number, p.file_path, p.status, p.created_at,
                  e.raw_json
           FROM notebook_pages p
           LEFT JOIN evaluations e ON e.page_id = p.id
           WHERE p.subject_id = ?
           ORDER BY p.upload_date, p.page_number""",
        (subject_id,),
    )
    page_rows = await pages_cursor.fetchall()

    # Group pages into one DailySession per upload_date.
    sessions_by_date = {}
    for row in page_rows:
        evaluation = (
            PageEvaluationResponse.model_validate_json(row["raw_json"]) if row["raw_json"] else None
        )

        page_item = PageItem(
            id=row["id"],
            subject_id=subject_id,
            subject_name=subject_row["name"],
            upload_date=row["upload_date"],
            page_number=row["page_number"],
            image_url=f"/uploads/{row['file_path']}",
            status=row["status"],
            evaluation=evaluation,
            created_at=row["created_at"],
        )

        if row["upload_date"] not in sessions_by_date:
            formatted = datetime.strptime(row["upload_date"], "%Y-%m-%d").strftime("%A, %b %d, %Y")
            sessions_by_date[row["upload_date"]] = DailySession(
                date=row["upload_date"],
                formatted_date=formatted,
                subject_id=subject_id,
                subject_name=subject_row["name"],
            )
        sessions_by_date[row["upload_date"]].pages.append(page_item)

    sessions = list(sessions_by_date.values())
    for session in sessions:
        scores = [p.evaluation.score for p in session.pages if p.evaluation]
        session.average_score = round(sum(scores) / len(scores), 1) if scores else None
        session.total_errors = sum(p.evaluation.total_mistakes for p in session.pages if p.evaluation)

    session_scores = [s.average_score for s in sessions if s.average_score is not None]
    overall_average = round(sum(session_scores) / len(session_scores), 1) if session_scores else None

    subject = SubjectResponse(
        id=subject_row["id"],
        name=subject_row["name"],
        color=subject_row["color"],
        description=subject_row["description"],
        page_count=len(page_rows),
        average_score=overall_average,
        last_updated=page_rows[-1]["created_at"] if page_rows else None,
    )

    return NotebookResponse(
        subject=subject,
        sessions=sessions,
        total_pages=len(page_rows),
        total_sessions=len(sessions),
        overall_average_score=overall_average,
    )


async def _fetch_pages_for_pdf(db: aiosqlite.Connection, subject_id: str, upload_date: str = None):
    """Fetch pages (with parsed evaluations) for a subject, optionally filtered to one day."""
    query = """SELECT p.page_number, p.upload_date, p.file_path, e.raw_json
               FROM notebook_pages p
               LEFT JOIN evaluations e ON e.page_id = p.id
               WHERE p.subject_id = ?"""
    params = [subject_id]
    if upload_date:
        query += " AND p.upload_date = ?"
        params.append(upload_date)
    query += " ORDER BY p.upload_date, p.page_number"

    cursor = await db.execute(query, params)
    rows = await cursor.fetchall()

    return [
        {
            "page_number": row["page_number"],
            "upload_date": row["upload_date"],
            "image_path": UPLOADS_DIR / row["file_path"],
            "evaluation": PageEvaluationResponse.model_validate_json(row["raw_json"]) if row["raw_json"] else None,
        }
        for row in rows
    ]


async def _get_owned_subject_name(db: aiosqlite.Connection, subject_id: str, student_id: str) -> str:
    """Look up a subject's name, only if it belongs to the given student."""
    cursor = await db.execute(
        "SELECT name FROM subjects WHERE id = ? AND student_id = ?",
        (subject_id, student_id),
    )
    row = await cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Subject not found")
    return row["name"]


@app.get("/subjects/{subject_id}/notebook/pdf")
async def download_notebook_pdf(
    subject_id: str,
    db: aiosqlite.Connection = Depends(get_db),
    student_id: str = Depends(get_student_id),
):
    """Download the full merged notebook (every day's pages) for a subject as one PDF."""
    subject_name = await _get_owned_subject_name(db, subject_id, student_id)

    pages = await _fetch_pages_for_pdf(db, subject_id)
    if not pages:
        raise HTTPException(status_code=404, detail="No pages uploaded yet for this subject")

    pdf_bytes = build_notebook_pdf(subject_name, pages)
    filename = f"{subject_name}_notebook.pdf".replace(" ", "_")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/subjects/{subject_id}/sessions/{upload_date}/pdf")
async def download_session_pdf(
    subject_id: str,
    upload_date: str,
    db: aiosqlite.Connection = Depends(get_db),
    student_id: str = Depends(get_student_id),
):
    """Download a single day's uploaded pages for a subject as one PDF."""
    subject_name = await _get_owned_subject_name(db, subject_id, student_id)

    pages = await _fetch_pages_for_pdf(db, subject_id, upload_date)
    if not pages:
        raise HTTPException(status_code=404, detail="No pages uploaded on this date")

    pdf_bytes = build_notebook_pdf(subject_name, pages)
    filename = f"{subject_name}_{upload_date}.pdf".replace(" ", "_")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/pages/{page_id}/pdf")
async def download_page_pdf(
    page_id: str,
    db: aiosqlite.Connection = Depends(get_db),
    student_id: str = Depends(get_student_id),
):
    """Download a single notebook page (with pins) and its evaluation as a PDF."""
    cursor = await db.execute(
        """SELECT p.page_number, p.upload_date, p.file_path, s.name AS subject_name, e.raw_json
           FROM notebook_pages p
           JOIN subjects s ON s.id = p.subject_id
           LEFT JOIN evaluations e ON e.page_id = p.id
           WHERE p.id = ? AND p.student_id = ?""",
        (page_id, student_id),
    )
    row = await cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Page not found")

    page = {
        "page_number": row["page_number"],
        "upload_date": row["upload_date"],
        "image_path": UPLOADS_DIR / row["file_path"],
        "evaluation": PageEvaluationResponse.model_validate_json(row["raw_json"]) if row["raw_json"] else None,
    }

    pdf_bytes = build_notebook_pdf(row["subject_name"], [page])
    filename = f"{row['subject_name']}_page{row['page_number']}_{row['upload_date']}.pdf".replace(" ", "_")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
