from typing import Optional, Literal
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
