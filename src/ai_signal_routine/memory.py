from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import SignalItem
from .utils import canonicalize_url


VALID_DECISIONS = ["unreviewed", "watch", "test", "implement", "archive"]
VALID_PRIORITIES = ["low", "medium", "high"]


def default_memory() -> dict[str, Any]:
    return {"updated_at": None, "signals": {}}


def default_operator_state() -> dict[str, Any]:
    return {
        "decision": "unreviewed",
        "priority": "medium",
        "notes": "",
        "next_action": "",
        "linked_project": "",
        "updated_at": None,
    }


def load_memory(path: Path) -> dict[str, Any]:
    if not path.exists():
        return default_memory()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default_memory()
    if "signals" not in payload or not isinstance(payload["signals"], dict):
        payload["signals"] = {}
    if "updated_at" not in payload:
        payload["updated_at"] = None
    return payload


def ensure_memory_file(path: Path) -> dict[str, Any]:
    memory = load_memory(path)
    if not path.exists():
        save_memory(path, memory)
    return memory


def save_memory(path: Path, memory: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    memory["updated_at"] = datetime.now(timezone.utc).isoformat()
    path.write_text(json.dumps(memory, indent=2), encoding="utf-8")


def get_operator_state(memory: dict[str, Any], url: str) -> dict[str, Any]:
    key = canonicalize_url(url)
    state = default_operator_state()
    stored = memory.get("signals", {}).get(key, {})
    if isinstance(stored, dict):
        for field in state:
            if field in stored:
                state[field] = stored[field]
    return state


def attach_memory_to_items(items: list[SignalItem], memory: dict[str, Any]) -> list[SignalItem]:
    for item in items:
        item.metadata["operator"] = get_operator_state(memory, item.url)
    return items


def enrich_payload_with_memory(payload: dict[str, Any], memory: dict[str, Any]) -> dict[str, Any]:
    items = payload.get("items", [])
    for item in items:
        item["operator"] = get_operator_state(memory, item.get("url", ""))
    payload["memory_summary"] = summarize_payload_items(items)
    return payload


def summarize_items(items: list[SignalItem]) -> dict[str, int]:
    counts = {decision: 0 for decision in VALID_DECISIONS}
    for item in items:
        operator = item.metadata.get("operator", {})
        decision = operator.get("decision", "unreviewed")
        counts[decision] = counts.get(decision, 0) + 1
    counts["reviewed"] = sum(counts[decision] for decision in VALID_DECISIONS if decision != "unreviewed")
    counts["total"] = len(items)
    return counts


def summarize_payload_items(items: list[dict[str, Any]]) -> dict[str, int]:
    counts = {decision: 0 for decision in VALID_DECISIONS}
    for item in items:
        operator = item.get("operator", {})
        decision = operator.get("decision", "unreviewed")
        counts[decision] = counts.get(decision, 0) + 1
    counts["reviewed"] = sum(counts[decision] for decision in VALID_DECISIONS if decision != "unreviewed")
    counts["total"] = len(items)
    return counts


def update_signal_memory(
    memory: dict[str, Any],
    *,
    url: str,
    title: str,
    source: str,
    decision: str,
    priority: str,
    notes: str,
    next_action: str,
    linked_project: str,
) -> dict[str, Any]:
    if decision not in VALID_DECISIONS:
        decision = "unreviewed"
    if priority not in VALID_PRIORITIES:
        priority = "medium"
    key = canonicalize_url(url)
    entry = get_operator_state(memory, url)
    entry.update(
        {
            "decision": decision,
            "priority": priority,
            "notes": notes.strip(),
            "next_action": next_action.strip(),
            "linked_project": linked_project.strip(),
            "title": title,
            "source": source,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    memory.setdefault("signals", {})[key] = entry
    return entry
