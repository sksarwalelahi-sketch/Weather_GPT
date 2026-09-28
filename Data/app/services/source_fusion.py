from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True)
class FusionScore:
    score: float
    label: str
    sources: list[str]
    method: str

    def as_dict(self) -> dict[str, object]:
        return {
            "confidence": self.score,
            "confidence_label": self.label,
            "sources": self.sources,
            "fusion_method": self.method,
        }


def _label(score: float) -> str:
    if score >= 0.85:
        return "high"
    if score >= 0.65:
        return "moderate"
    return "low"


def score_sources(
    sources: list[str],
    *,
    official: bool = False,
    retrieved_at: datetime | None = None,
    corroborating_sources: int = 0,
) -> FusionScore:
    unique_sources = list(dict.fromkeys(source for source in sources if source))
    if not unique_sources:
        return FusionScore(0.0, "low", [], "no-evidence")

    score = 0.95 if official else min(0.65 + 0.10 * (len(unique_sources) - 1), 0.85)
    if corroborating_sources:
        score += min(0.10, 0.05 * corroborating_sources)

    if retrieved_at is not None:
        timestamp = retrieved_at.astimezone(UTC) if retrieved_at.tzinfo else retrieved_at.replace(tzinfo=UTC)
        age_hours = max(0.0, (datetime.now(UTC) - timestamp).total_seconds() / 3600)
        if age_hours > 48:
            score -= 0.25
        elif age_hours > 12:
            score -= 0.10

    score = round(max(0.0, min(score, 1.0)), 2)
    method = "official-source" if official else (
        "multi-source-corroboration" if len(unique_sources) > 1 or corroborating_sources else "single-source"
    )
    return FusionScore(score, _label(score), unique_sources, method)


def single_source_score(source: str, retrieved_at: datetime | None = None) -> dict[str, object]:
    return score_sources([source], retrieved_at=retrieved_at).as_dict()
