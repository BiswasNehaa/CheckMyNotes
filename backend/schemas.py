from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class MistakePin(BaseModel):
    """
    Represents a single pinpointed mistake, warning, or good step
    with exact (x, y) coordinates on the handwritten notebook page image.
    """
    id: str = Field(..., description="Unique pin ID, e.g. 'pin-1'")
    x_percent: float = Field(..., description="Horizontal coordinate (0% to 100%) from the left edge of the page")
    y_percent: float = Field(..., description="Vertical coordinate (0% to 100%) from the top edge of the page")
    severity: Literal["error", "warning", "good"] = Field("error", description="Type: 'error' (red pin), 'warning' (yellow pin), 'good' (green pin)")
    step_number: Optional[int] = Field(None, description="Step number in the solution if applicable (e.g., Step 3)")
    title: str = Field(..., description="Short summary title of the remark")
    explanation: str = Field(..., description="Detailed explanation of what went wrong or why it is good")
    corrected_step: Optional[str] = Field(None, description="The correct mathematical formula or step")
    concept_refresher: Optional[str] = Field(None, description="Key rule, formula, or concept to remember")

class PageEvaluationResponse(BaseModel):
    """
    Represents the full AI evaluation report for a single notebook page.
    Contains the overall grade, teacher feedback, and all pinpointed mistakes.
    """
    score: float = Field(..., description="Numerical score out of 10 (e.g. 8.5)")
    grade_label: str = Field(..., description="Friendly letter grade label, e.g. 'A - Great Work'")
    summary: str = Field(..., description="Overall teacher summary remark for the student")
    total_mistakes: int = Field(0, description="Count of critical calculation/conceptual mistakes")
    total_warnings: int = Field(0, description="Count of minor formatting/notation warnings")
    mistakes: List[MistakePin] = Field(default_factory=list, description="List of all visual pins on the page")
    key_concepts_tested: List[str] = Field(default_factory=list, description="Topics and formulas identified on the page")
    strengths: List[str] = Field(default_factory=list, description="List of what the student did well")
    areas_to_improve: List[str] = Field(default_factory=list, description="Actionable tips for the student to practice")

class SubjectCreate(BaseModel):
    """Payload sent when a student creates a new subject (e.g. Mathematics)."""
    name: str = Field(..., description="Subject name e.g. 'Mathematics' or 'Physics'")
    color: str = Field("#4F46E5", description="Hex color code for UI cards e.g. '#3B82F6'")
    description: Optional[str] = Field(None, description="Optional description or syllabus topics")

class SubjectResponse(BaseModel):
    """Data sent to the frontend when listing subjects with stats."""
    id: str = Field(..., description="Unique subject ID e.g. 'sub_math'")
    name: str = Field(..., description="Subject name")
    color: str = Field(..., description="Hex color code")
    description: Optional[str] = Field(None, description="Subject description")
    page_count: int = Field(0, description="Total number of uploaded pages in this subject")
    average_score: Optional[float] = Field(None, description="Average AI score across all pages")
    last_updated: Optional[str] = Field(None, description="Timestamp of the most recent page upload")


class PageItem(BaseModel):
    """Represents one uploaded notebook page with its image URL and AI evaluation."""
    id: str = Field(..., description="Unique page ID e.g. 'page_a1b2c3d4'")
    subject_id: str = Field(..., description="Subject code this page belongs to")
    subject_name: Optional[str] = Field(None, description="Subject name e.g. 'Mathematics'")
    upload_date: str = Field(..., description="Date uploaded in YYYY-MM-DD format e.g. '2026-09-04'")
    page_number: int = Field(1, description="Page sequence number within that day's session")
    image_url: str = Field(..., description="URL path to view the uploaded handwritten image")
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail URL for quick preview")
    status: Literal["pending", "processing", "completed", "failed"] = Field("pending", description="AI checking status")
    evaluation: Optional[PageEvaluationResponse] = Field(None, description="Full AI evaluation results and mistake pins")
    created_at: str = Field(..., description="Timestamp when the page was uploaded")

class DailySession(BaseModel):
    """Groups all pages uploaded on a single calendar day for a subject."""
    date: str = Field(..., description="Date string e.g. '2026-09-04'")
    formatted_date: str = Field(..., description="Human-friendly date e.g. 'Thursday, Sep 4, 2026'")
    subject_id: str = Field(..., description="Subject code")
    subject_name: str = Field(..., description="Subject name")
    pages: List[PageItem] = Field(default_factory=list, description="Array of pages uploaded on this day")
    average_score: Optional[float] = Field(None, description="Average AI score for this day's pages")
    total_errors: int = Field(0, description="Total mistakes found on this day's homework")

class NotebookResponse(BaseModel):
    """Complete subject notebook containing all daily sessions and cumulative statistics."""
    subject: SubjectResponse = Field(..., description="Subject metadata and stats")
    sessions: List[DailySession] = Field(default_factory=list, description="List of all daily upload sessions")
    total_pages: int = Field(0, description="Total pages across all sessions in this subject")
    total_sessions: int = Field(0, description="Total number of days notes were uploaded")
    overall_average_score: Optional[float] = Field(None, description="Cumulative grade average for this subject")

class ApiKeyConfigRequest(BaseModel):
    """Allows students to configure their own free Gemini / Groq API key in Settings."""
    groq_api_key: Optional[str] = Field(None, description="Groq API Key (Free tier LLaMA 3.2 Vision)")
    gemini_api_key: Optional[str] = Field(None, description="Google Gemini API Key (Free tier Gemini 1.5 Flash)")
    preferred_provider: Literal["groq", "gemini", "auto", "simulated"] = Field("auto", description="AI provider preference")



