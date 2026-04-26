from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class SignalItem:
    title: str
    url: str
    source: str
    group: str
    source_type: str
    published_at: datetime | None = None
    summary: str = ""
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    score: float = 0.0
    rationale: list[str] = field(default_factory=list)

    def age_days(self, now: datetime | None = None) -> float | None:
        if not self.published_at:
            return None
        reference = now or datetime.now(timezone.utc)
        delta = reference - self.published_at
        return max(delta.total_seconds() / 86400, 0.0)

    def published_label(self) -> str:
        if not self.published_at:
            return "Unknown"
        return self.published_at.astimezone(timezone.utc).strftime("%Y-%m-%d")


@dataclass(slots=True)
class MiniProject:
    title: str
    why_now: str
    build_scope: str
    stack: str
    success_metric: str
    prompt_seed: str
