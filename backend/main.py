import uuid
from datetime import datetime
from pathlib import Path
from typing import List

import aiofiles
import aiosqlite
from fastapi import FastAPI, Depends, File, Form, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles

from ai_service import evaluate_page
from database import init_db, get_db, UPLOADS_DIR
from schemas import (
    DailySession,
    NotebookResponse,
    PageEvaluationResponse,
    PageItem,
    SubjectCreate,
    SubjectResponse,
)

# Single default student used for now instead of real authentication.
DEFAULT_STUDENT_ID = "default_student"

app = FastAPI(title="Acadine API")

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


@app.post("/subjects", response_model=SubjectResponse)
async def create_subject(subject: SubjectCreate, db: aiosqlite.Connection = Depends(get_db)):
    """Create a new subject (e.g. Mathematics) for the default student."""
    subject_id = f"sub_{uuid.uuid4().hex[:8]}"
    await db.execute(
        "INSERT INTO subjects (id, student_id, name, color, description) VALUES (?, ?, ?, ?, ?)",
        (subject_id, DEFAULT_STUDENT_ID, subject.name, subject.color, subject.description),
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
async def list_subjects(db: aiosqlite.Connection = Depends(get_db)):
    """List all subjects for the default student."""
    cursor = await db.execute(
        "SELECT id, name, color, description FROM subjects WHERE student_id = ?",
        (DEFAULT_STUDENT_ID,),
    )
    rows = await cursor.fetchall()

    return [
        SubjectResponse(
            id=row["id"],
            name=row["name"],
            color=row["color"],
            description=row["description"],
            page_count=0,
            average_score=None,
            last_updated=None,
        )
        for row in rows
    ]


@app.post("/pages/upload")
async def upload_pages(
    subject_id: str = Form(...),
    upload_date: str = Form(...),
    files: List[UploadFile] = File(...),
    db: aiosqlite.Connection = Depends(get_db),
):
    """Save uploaded notebook page images and create a 'pending' record for each."""
    uploaded = []

    for index, file in enumerate(files, start=1):
        page_id = f"page_{uuid.uuid4().hex[:8]}"
        file_name = f"{page_id}{Path(file.filename).suffix}"

        contents = await file.read()
        async with aiofiles.open(UPLOADS_DIR / file_name, "wb") as out_file:
            await out_file.write(contents)

        await db.execute(
            """INSERT INTO notebook_pages
               (id, student_id, subject_id, upload_date, page_number, file_path, status)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (page_id, DEFAULT_STUDENT_ID, subject_id, upload_date, index, file_name, "pending"),
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
    """Run the (simulated) AI evaluation on a single uploaded page and store the result."""
    cursor = await db.execute("SELECT id FROM notebook_pages WHERE id = ?", (page_id,))
    page = await cursor.fetchone()
    if page is None:
        raise HTTPException(status_code=404, detail="Page not found")

    evaluation = evaluate_page(page_id)

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
async def get_subject_notebook(subject_id: str, db: aiosqlite.Connection = Depends(get_db)):
    """Return all uploaded pages (with evaluations, if any) for a subject, grouped by day."""
    subject_cursor = await db.execute(
        "SELECT id, name, color, description FROM subjects WHERE id = ? AND student_id = ?",
        (subject_id, DEFAULT_STUDENT_ID),
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
