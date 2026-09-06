import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

import aiosqlite

import database
import main
from schemas import PageEvaluationResponse


CREATE_TEST_TABLES = """
CREATE TABLE notebook_pages (
    id TEXT PRIMARY KEY,
    student_id TEXT NOT NULL,
    subject_id TEXT NOT NULL,
    upload_date TEXT NOT NULL,
    page_number INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    image_hash TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE evaluations (
    id TEXT PRIMARY KEY,
    page_id TEXT UNIQUE NOT NULL,
    score REAL NOT NULL,
    grade_label TEXT NOT NULL,
    summary TEXT NOT NULL,
    total_mistakes INTEGER DEFAULT 0,
    total_warnings INTEGER DEFAULT 0,
    raw_json TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


def evaluation(summary: str) -> PageEvaluationResponse:
    return PageEvaluationResponse(score=8, grade_label="B", summary=summary)


class EvaluationCacheTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.db = await aiosqlite.connect(":memory:")
        self.db.row_factory = aiosqlite.Row
        await self.db.executescript(CREATE_TEST_TABLES)

    async def asyncTearDown(self) -> None:
        await self.db.close()

    async def add_page(self, page_id: str, student_id: str) -> None:
        await self.db.execute(
            """INSERT INTO notebook_pages
               (id, student_id, subject_id, upload_date, page_number, file_path, image_hash)
               VALUES (?, ?, 'math', '2026-09-07', 1, 'page.png', 'same-hash')""",
            (page_id, student_id),
        )

    async def add_evaluation(self, page_id: str, result: PageEvaluationResponse) -> None:
        await self.db.execute(
            """INSERT INTO evaluations
               (id, page_id, score, grade_label, summary, raw_json)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (f"eval-{page_id}", page_id, result.score, result.grade_label, result.summary,
             result.model_dump_json()),
        )
        await self.db.commit()

    async def test_identical_images_from_different_students_are_not_shared(self) -> None:
        await self.add_page("other-page", "student-b")
        await self.add_page("target-page", "student-a")
        await self.add_evaluation("other-page", evaluation("student-b cached result"))
        fresh = evaluation("student-a fresh result")

        with patch.object(main, "evaluate_page", AsyncMock(return_value=fresh)) as evaluate:
            result = await main.evaluate_uploaded_page("target-page", self.db)

        self.assertEqual(result.summary, "student-a fresh result")
        evaluate.assert_awaited_once()

    async def test_identical_images_for_same_student_reuse_the_cache(self) -> None:
        await self.add_page("previous-page", "student-a")
        await self.add_page("target-page", "student-a")
        await self.add_evaluation("previous-page", evaluation("student-a cached result"))

        with patch.object(main, "evaluate_page", AsyncMock()) as evaluate:
            result = await main.evaluate_uploaded_page("target-page", self.db)

        self.assertEqual(result.summary, "student-a cached result")
        evaluate.assert_not_awaited()


class DatabaseIndexTests(unittest.IsolatedAsyncioTestCase):
    async def test_image_hash_index_is_created_and_used(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            test_db = Path(temp_dir) / "test.db"
            with patch.object(database, "DB_PATH", test_db):
                await database.init_db()

            async with aiosqlite.connect(test_db) as db:
                indexes = await (await db.execute("PRAGMA index_list('notebook_pages')")).fetchall()
                self.assertIn("idx_notebook_pages_hash", {row[1] for row in indexes})
                plan = await (
                    await db.execute(
                        "EXPLAIN QUERY PLAN SELECT * FROM notebook_pages WHERE image_hash = ? AND student_id = ?",
                        ("same-hash", "student-a"),
                    )
                ).fetchall()

        self.assertTrue(any("idx_notebook_pages_hash" in row[3] for row in plan), plan)


if __name__ == "__main__":
    unittest.main()
