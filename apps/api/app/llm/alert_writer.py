"""LLM-powered alert message generator.

Receives a list of AbnormalFinding objects and calls the LLM to produce
a concise, human-readable alert message. Falls back to a local message when
the configured LLM provider is unavailable so logging health data never fails.
"""

import logging
from dataclasses import dataclass
from typing import Literal

from app.llm.client import call_llm
from app.models.user import UserProfile

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# AbnormalFinding - produced by per-indicator check functions
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
You are a health assistant writing brief, supportive alerts for a personal
health tracker. Given one or more abnormal health findings, write a single
concise alert message (2-4 sentences).
- Be factual and calm - do not alarm the user unnecessarily.
- Mention each finding clearly.
- Where relevant, distinguish between immediate readings and multi-day trends.
- End with one actionable suggestion.
Do NOT use markdown formatting in your response.
"""


def _fallback_action(metric: str) -> str:
    actions = {
        "basic_indicators": (
            "Recheck your measurements and keep tracking over the next few days."
        ),
        "diet": (
            "Review today's meals and continue logging so we can watch for a pattern."
        ),
        "sleep": (
            "Try to protect your sleep routine tonight and keep logging the next "
            "few days."
        ),
        "exercise": (
            "Ease intensity if needed and monitor how your body feels over the "
            "next few days."
        ),
        "period": (
            "Keep tracking your cycle details and consider medical advice if this "
            "continues."
        ),
    }
    return actions.get(
        metric,
        (
            "Keep monitoring this metric and reach out to a clinician if it "
            "continues."
        ),
    )


def _fallback_finding_sentence(finding: AbnormalFinding) -> str:
    mode_label = (
        "today's reading"
        if finding.evaluation_mode == "immediate"
        else "your recent trend"
    )
    metric_label = finding.metric.replace("_", " ")
    description = finding.raw_description.strip()
    if description:
        description = description[:1].lower() + description[1:]
    return f"{mode_label} for {metric_label} shows {description}."


def _build_fallback_alert_message(
    findings: list[AbnormalFinding],
    user: UserProfile,
) -> str:
    lead = f"{user.name}, I noticed a health update worth reviewing."
    detail_sentences = [
        _fallback_finding_sentence(finding)
        for finding in findings[:2]
    ]

    if len(findings) > 2:
        detail_sentences.append(
            f"There are {len(findings) - 2} additional flagged finding(s) "
            "in this update."
        )

    action = _fallback_action(findings[0].metric)
    return " ".join([lead, *detail_sentences, action])


def _build_alert_user_message(
    findings: list[AbnormalFinding],
    user: UserProfile,
) -> str:
    sex_label = "Male" if user.sex == "M" else "Female"
    lines = [f"User: {user.name}, age {user.age}, sex {sex_label}."]
    lines.append("Abnormal findings:")
    for finding in findings:
        mode_label = (
            "immediate reading"
            if finding.evaluation_mode == "immediate"
            else "trend over recent days"
        )
        lines.append(
            f"  - [{finding.severity.upper()}] {finding.metric} "
            f"({mode_label}): {finding.raw_description}"
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
    try:
        return await call_llm(_ALERT_SYSTEM, user_msg)
    except Exception as exc:
        logger.warning(
            "LLM alert generation unavailable; using local fallback message: %s",
            exc,
        )
        return _build_fallback_alert_message(findings, user)
