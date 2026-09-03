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

