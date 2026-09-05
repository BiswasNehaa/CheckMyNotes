from pathlib import Path
from typing import List, Optional

import pymupdf

from schemas import PageEvaluationResponse

SEVERITY_COLORS = {
    "error": (0.86, 0.15, 0.15),
    "warning": (0.85, 0.47, 0.02),
    "good": (0.09, 0.64, 0.29),
}

PAGE_WIDTH = 595   # A4 width in points
PAGE_HEIGHT = 842  # A4 height in points
MARGIN = 40
TEXT_WIDTH = PAGE_WIDTH - (2 * MARGIN)


def _wrap_and_insert(page, x: float, y: float, text: str, fontsize: float = 10, line_height: float = 14) -> float:
    """Insert text word-wrapped to fit the page width. Returns the y position after the text."""
    words = text.split()
    line = ""
    for word in words:
        candidate = f"{line} {word}".strip()
        if pymupdf.get_text_length(candidate, fontsize=fontsize) > TEXT_WIDTH and line:
            page.insert_text((x, y), line, fontsize=fontsize)
            y += line_height
            line = word
        else:
            line = candidate
    if line:
        page.insert_text((x, y), line, fontsize=fontsize)
        y += line_height
    return y


def _add_image_page(doc, image_path: Path, evaluation: Optional[PageEvaluationResponse]):
    """Add a page showing the notebook photo with numbered mistake pins drawn on top."""
    page = doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
    image_rect = pymupdf.Rect(MARGIN, MARGIN, PAGE_WIDTH - MARGIN, PAGE_HEIGHT - MARGIN)
    page.insert_image(image_rect, filename=str(image_path))

    if not evaluation:
        return

    for index, mistake in enumerate(evaluation.mistakes, start=1):
        center = (
            image_rect.x0 + (mistake.x_percent / 100) * image_rect.width,
            image_rect.y0 + (mistake.y_percent / 100) * image_rect.height,
        )
        color = SEVERITY_COLORS.get(mistake.severity, (0.5, 0.5, 0.5))
        page.draw_circle(center, radius=11, color=(1, 1, 1), fill=color, width=1.5)
        page.insert_text((center[0] - 3, center[1] + 3), str(index), fontsize=9, color=(1, 1, 1))


def _add_evaluation_page(doc, subject_name: str, page_number: int, upload_date: str, evaluation: Optional[PageEvaluationResponse]):
    """Add a text page with the score, summary, and full explanation for every mistake pin."""
    page = doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
    y = MARGIN

    page.insert_text((MARGIN, y), f"{subject_name} - Page {page_number} ({upload_date})", fontsize=14)
    y += 26

    if not evaluation:
        page.insert_text((MARGIN, y), "This page has not been evaluated yet.", fontsize=11)
        return

    page.insert_text((MARGIN, y), f"Score: {evaluation.score}/10 - {evaluation.grade_label}", fontsize=12)
    y += 22
    y = _wrap_and_insert(page, MARGIN, y, evaluation.summary, fontsize=11)
    y += 12

    for index, mistake in enumerate(evaluation.mistakes, start=1):
        if y > PAGE_HEIGHT - MARGIN - 60:
            page = doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
            y = MARGIN

        page.insert_text((MARGIN, y), f"{index}. {mistake.title} ({mistake.severity})", fontsize=11)
        y += 16
        y = _wrap_and_insert(page, MARGIN + 12, y, mistake.explanation, fontsize=10)
        if mistake.corrected_step:
            y = _wrap_and_insert(page, MARGIN + 12, y, f"Correction: {mistake.corrected_step}", fontsize=10)
        if mistake.concept_refresher:
            y = _wrap_and_insert(page, MARGIN + 12, y, f"Tip: {mistake.concept_refresher}", fontsize=10)
        y += 10


def build_notebook_pdf(subject_name: str, pages: List[dict]) -> bytes:
    """
    Build a self-contained PDF for a list of notebook pages.
    Each dict in `pages` needs: image_path (Path), page_number (int),
    upload_date (str), evaluation (PageEvaluationResponse or None).
    Every notebook page becomes an image page (with pins) followed by a text page
    (full evaluation), so the PDF works standalone without the app.
    """
    doc = pymupdf.open()
    for page in pages:
        _add_image_page(doc, page["image_path"], page["evaluation"])
        _add_evaluation_page(doc, subject_name, page["page_number"], page["upload_date"], page["evaluation"])

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes
