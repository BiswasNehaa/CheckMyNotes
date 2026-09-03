import os
import aiosqlite
import json
from pathlib import Path
from typing import List, Optional, Dict, Any

# Paths for SQLite database and uploaded images
DB_PATH = Path(__file__).resolve().parent / "acadine_notebooks.db"
UPLOADS_DIR = Path(__file__).resolve().parent / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

async def get_db():
    """
    FastAPI Database Dependency.
    Opens an async connection to SQLite for an incoming API request
    and automatically closes it when the request finishes.
    """
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row  # Enables column access by name (e.g. row['name'])
    try:
        yield db
    finally:
        await db.close()

async def init_db():
    """
    Initializes database tables on application startup.
    Creates tables for: students, subjects, notebook_pages, evaluations, and settings.
    Also seeds default subjects if the database is brand new.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        # 1. Students Table (stores student profiles)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                grade TEXT NOT NULL,
                avatar TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 2. Subjects Table (stores subjects like Math, Physics, Chem)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS subjects (
                id TEXT PRIMARY KEY,
                student_id TEXT NOT NULL,
                name TEXT NOT NULL,
                color TEXT DEFAULT '#4F46E5',
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 3. Notebook Pages Table (stores uploaded page photos, dates, and AI status)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS notebook_pages (
                id TEXT PRIMARY KEY,
                student_id TEXT NOT NULL,
                subject_id TEXT NOT NULL,
                upload_date TEXT NOT NULL,
                page_number INTEGER NOT NULL,
                file_path TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
            )
        """)

        # 4. Evaluations Table (stores AI scores, summaries, and mistake pins JSON)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS evaluations (
                id TEXT PRIMARY KEY,
                page_id TEXT UNIQUE NOT NULL,
                score REAL NOT NULL,
                grade_label TEXT NOT NULL,
                summary TEXT NOT NULL,
                total_mistakes INTEGER DEFAULT 0,
                total_warnings INTEGER DEFAULT 0,
                raw_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (page_id) REFERENCES notebook_pages(id) ON DELETE CASCADE
            )
        """)

        # 5. Settings Table (stores API keys and preferences dynamically)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

        await db.commit()

