import uuid
from typing import List

import aiosqlite
from fastapi import FastAPI, Depends

from database import init_db, get_db
from schemas import SubjectCreate, SubjectResponse

# Single default student used for now instead of real authentication.
DEFAULT_STUDENT_ID = "default_student"

app = FastAPI(title="Acadine API")


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
