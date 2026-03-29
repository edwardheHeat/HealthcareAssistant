"""LLM-powered alert message generator.

Receives a list of AbnormalFinding objects and calls the LLM to produce
a concise, human-readable alert message. Uses call_llm() from llm/client.py.
"""

from dataclasses import dataclass
from typing import Literal

from app.llm.client import call_llm
from app.models.user import UserProfile


# ---------------------------------------------------------------------------
# AbnormalFinding — produced by per-indicator check functions
# ---------------------------------------------------------------------------

@dataclass
class AbnormalFinding:
    """Structured description of one abnormal reading.

    raw_description contains factual data only (e.g. "BMI=31.2, threshold=30").
    The LLM converts this into natural language.
    """

    metric: str
    severity: Literal["warning", "critical"]
    evaluation_mode: Literal["immediate", "trend"]
    raw_description: str


# ---------------------------------------------------------------------------
# Prompt builder (also registered in llm/prompts.py for consistency)
# ---------------------------------------------------------------------------

_ALERT_SYSTEM = """\
You are a health assistant writing brief, supportive alerts for a personal health tracker.
Given one or more abnormal health findings, write a single concise alert message (2–4 sentences).
- Be factual and calm — do not alarm the user unnecessarily.
- Mention each finding clearly.
- Where relevant, distinguish between immediate readings and multi-day trends.
- End with one actionable suggestion.
Do NOT use markdown formatting in your response.
"""

def _build_alert_user_message(
    findings: list[AbnormalFinding],
    user: UserProfile,
) -> str:
    lines = [f"User: {user.name}, age {user.age}, sex {'Male' if user.sex == 'M' else 'Female'}."]
    lines.append("Abnormal findings:")
    for f in findings:
        mode_label = "immediate reading" if f.evaluation_mode == "immediate" else "trend over recent days"
        lines.append(
            f"  - [{f.severity.upper()}] {f.metric} ({mode_label}): {f.raw_description}"
        )
    lines.append("\nWrite the alert message now.")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def generate_alert_message(
    findings: list[AbnormalFinding],
    user: UserProfile,
) -> str:
    """Call the LLM and return a human-readable alert message string."""
    if not findings:
        return ""
    user_msg = _build_alert_user_message(findings, user)
    return await call_llm(_ALERT_SYSTEM, user_msg)
