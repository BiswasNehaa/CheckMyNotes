import asyncio
import base64
import json
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv

from schemas import PageEvaluationResponse

load_dotenv()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "qwen/qwen3.6-27b")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# Retry delays (seconds) for transient failures / rate limits (HTTP 429).
RETRY_DELAYS = [0, 1, 3, 6]

EVALUATION_PROMPT = """You are a strict but encouraging teacher checking a student's handwritten notebook page.

Look at the image and evaluate the work. Respond with ONLY a single JSON object (no markdown, no extra text) matching this exact structure:

{
  "score": <number 0-10>,
  "grade_label": "<short label e.g. 'B - Good Effort'>",
  "summary": "<1-2 sentence overall summary>",
  "mistakes": [
    {
      "id": "pin-1",
      "x_percent": <0-100, horizontal position of this point on the page>,
      "y_percent": <0-100, vertical position of this point on the page>,
      "severity": "error" | "warning" | "good",
      "title": "<short title>",
      "explanation": "<what is wrong or good, and why>",
      "corrected_step": "<corrected version, or null>",
      "concept_refresher": "<key concept/formula to remember, or null>"
    }
  ],
  "key_concepts_tested": ["<topic>"],
  "strengths": ["<what the student did well>"],
  "areas_to_improve": ["<actionable tip>"]
}

Include 1-5 mistakes/highlights total, mixing severities as appropriate. Coordinates are percentages measured from the top-left corner of the image."""


def _encode_image(image_path: Path) -> str:
    """Read an image file and return it as a base64 data URL for the AI request."""
    data = image_path.read_bytes()
    encoded = base64.b64encode(data).decode("utf-8")
    suffix = image_path.suffix.lower().lstrip(".") or "jpeg"
    return f"data:image/{suffix};base64,{encoded}"


def _parse_evaluation_json(content: str) -> PageEvaluationResponse:
    """Extract the JSON object from the model's reply and validate it against our schema."""
    start = content.find("{")
    end = content.rfind("}")
    data = json.loads(content[start : end + 1])

    mistakes = data.get("mistakes", [])
    data.setdefault("total_mistakes", sum(1 for m in mistakes if m.get("severity") == "error"))
    data.setdefault("total_warnings", sum(1 for m in mistakes if m.get("severity") == "warning"))

    return PageEvaluationResponse.model_validate(data)


async def call_groq_vision(image_path: Path) -> PageEvaluationResponse:
    """Send the page image to Groq's vision model and return the parsed evaluation."""
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": EVALUATION_PROMPT},
                    {"type": "image_url", "image_url": {"url": _encode_image(image_path)}},
                ],
            }
        ],
        "max_completion_tokens": 900,
        "temperature": 0.2,
        "reasoning_effort": "none",
    }
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}

    last_error = None
    async with httpx.AsyncClient(timeout=30) as client:
        for delay in RETRY_DELAYS:
            if delay:
                await asyncio.sleep(delay)
            try:
                response = await client.post(GROQ_URL, json=payload, headers=headers)
                if response.status_code == 429:
                    last_error = "rate limited (429)"
                    continue
                response.raise_for_status()
                content = response.json()["choices"][0]["message"]["content"]
                return _parse_evaluation_json(content)
            except Exception as exc:
                last_error = str(exc)

    raise RuntimeError(f"Groq vision call failed after retries: {last_error}")


async def evaluate_page(page_id: str, image_path: Path) -> PageEvaluationResponse:
    """
    Evaluate a notebook page using real Groq AI vision.
    Raises RuntimeError if no API key is configured, or the AI call fails/rate-limits
    even after retries — callers must surface this as "AI unavailable", not hide it.
    """
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is not configured")

    result = await call_groq_vision(image_path)
    print(f"[ai_service] REAL AI: Groq evaluation successful (page_id={page_id})")
    return result
