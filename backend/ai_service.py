import random

from schemas import PageEvaluationResponse, MistakePin

# Pool of sample remarks the simulator picks from.
SAMPLE_REMARKS = [
    {
        "title": "Sign error in step 2",
        "explanation": "You dropped a negative sign when moving the term across the equation.",
        "severity": "error",
        "corrected_step": "-2x = -8  ->  x = 4",
        "concept_refresher": "Moving a term to the other side flips its sign.",
    },
    {
        "title": "Messy handwriting",
        "explanation": "Step 3 is hard to read, which could cost marks in an exam.",
        "severity": "warning",
        "corrected_step": None,
        "concept_refresher": "Write numbers and operators with clear spacing.",
    },
    {
        "title": "Correct final answer",
        "explanation": "The final answer and units are correct.",
        "severity": "good",
        "corrected_step": None,
        "concept_refresher": None,
    },
]


def evaluate_page(page_id: str) -> PageEvaluationResponse:
    """
    Simulated AI evaluation (no real AI call yet).
    Uses page_id as a random seed so the same page always gets the same result.
    """
    rng = random.Random(page_id)
    score = round(rng.uniform(6.0, 9.5), 1)

    if score >= 9:
        grade_label = "A - Great Work"
    elif score >= 7.5:
        grade_label = "B - Good Effort"
    else:
        grade_label = "C - Needs Practice"

    num_remarks = rng.randint(1, 3)
    chosen = rng.sample(SAMPLE_REMARKS, num_remarks)

    mistakes = [
        MistakePin(
            id=f"pin-{i + 1}",
            x_percent=round(rng.uniform(10, 90), 1),
            y_percent=round(rng.uniform(10, 90), 1),
            severity=remark["severity"],
            title=remark["title"],
            explanation=remark["explanation"],
            corrected_step=remark["corrected_step"],
            concept_refresher=remark["concept_refresher"],
        )
        for i, remark in enumerate(chosen)
    ]

    total_mistakes = sum(1 for m in mistakes if m.severity == "error")
    total_warnings = sum(1 for m in mistakes if m.severity == "warning")

    return PageEvaluationResponse(
        score=score,
        grade_label=grade_label,
        summary="Simulated evaluation: overall solid work with a few points to review.",
        total_mistakes=total_mistakes,
        total_warnings=total_warnings,
        mistakes=mistakes,
        key_concepts_tested=["Linear equations"],
        strengths=["Clear final answer"],
        areas_to_improve=["Double-check sign changes"],
    )
