from __future__ import annotations

import csv
import hashlib
import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .utils import canonicalize_url


ACTION_DECISIONS = {"watch", "test", "implement"}

SCHEMA = """
CREATE TABLE IF NOT EXISTS briefing_runs (
    run_id TEXT PRIMARY KEY,
    generated_at TEXT NOT NULL,
    profile TEXT NOT NULL,
    item_count INTEGER NOT NULL,
    reviewed_count INTEGER NOT NULL,
    implement_count INTEGER NOT NULL,
    test_count INTEGER NOT NULL,
    watch_count INTEGER NOT NULL,
    archive_count INTEGER NOT NULL,
    unreviewed_count INTEGER NOT NULL,
    top_theme TEXT,
    avg_score REAL NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS signals (
    run_id TEXT NOT NULL,
    signal_key TEXT NOT NULL,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    source TEXT NOT NULL,
    group_name TEXT,
    source_type TEXT,
    published_at TEXT,
    score REAL NOT NULL,
    decision TEXT NOT NULL,
    priority TEXT,
    linked_project TEXT,
    next_action TEXT,
    tags_json TEXT NOT NULL,
    theme_hint TEXT,
    recorded_at TEXT NOT NULL,
    PRIMARY KEY (run_id, signal_key),
    FOREIGN KEY (run_id) REFERENCES briefing_runs(run_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS theme_counts (
    run_id TEXT NOT NULL,
    theme TEXT NOT NULL,
    count INTEGER NOT NULL,
    PRIMARY KEY (run_id, theme),
    FOREIGN KEY (run_id) REFERENCES briefing_runs(run_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_signals_decision ON signals(decision);
CREATE INDEX IF NOT EXISTS idx_signals_source ON signals(source);
CREATE INDEX IF NOT EXISTS idx_signals_recorded_at ON signals(recorded_at);
"""


def initialize_history_db(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with _connect(path) as connection:
        connection.executescript(SCHEMA)


def record_briefing(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    initialize_history_db(path)
    generated_at = str(payload.get("generated_at") or _now_iso())
    profile = str(payload.get("profile") or "AI Signal Routine")
    items = [item for item in payload.get("items", []) if isinstance(item, dict)]
    themes = [theme for theme in payload.get("themes", []) if isinstance(theme, dict)]
    summary = _memory_summary(payload, items)
    run_id = _run_id(profile, generated_at)
    avg_score = _average_score(items)
    top_theme = str(themes[0].get("theme")) if themes else None
    recorded_at = _now_iso()

    with _connect(path) as connection:
        connection.execute(
            """
            INSERT OR REPLACE INTO briefing_runs (
                run_id, generated_at, profile, item_count, reviewed_count,
                implement_count, test_count, watch_count, archive_count,
                unreviewed_count, top_theme, avg_score, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                generated_at,
                profile,
                len(items),
                _as_int(summary.get("reviewed")),
                _as_int(summary.get("implement")),
                _as_int(summary.get("test")),
                _as_int(summary.get("watch")),
                _as_int(summary.get("archive")),
                _as_int(summary.get("unreviewed")),
                top_theme,
                avg_score,
                recorded_at,
            ),
        )
        connection.execute("DELETE FROM signals WHERE run_id = ?", (run_id,))
        connection.execute("DELETE FROM theme_counts WHERE run_id = ?", (run_id,))
        for item in items:
            operator = item.get("operator") if isinstance(item.get("operator"), dict) else {}
            tags = item.get("tags") if isinstance(item.get("tags"), list) else []
            metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
            connection.execute(
                """
                INSERT OR REPLACE INTO signals (
                    run_id, signal_key, title, url, source, group_name, source_type,
                    published_at, score, decision, priority, linked_project,
                    next_action, tags_json, theme_hint, recorded_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    _signal_key(item),
                    str(item.get("title") or "Untitled signal"),
                    str(item.get("url") or ""),
                    str(item.get("source") or "Unknown source"),
                    _optional_text(item.get("group")),
                    _optional_text(item.get("source_type")),
                    _optional_text(item.get("published_at")),
                    float(item.get("score") or 0.0),
                    str(operator.get("decision") or "unreviewed"),
                    _optional_text(operator.get("priority")),
                    _optional_text(operator.get("linked_project")),
                    _optional_text(operator.get("next_action")),
                    json.dumps(tags),
                    _optional_text(metadata.get("category") or item.get("group")),
                    recorded_at,
                ),
            )
        for theme in themes:
            connection.execute(
                "INSERT OR REPLACE INTO theme_counts (run_id, theme, count) VALUES (?, ?, ?)",
                (run_id, str(theme.get("theme") or "unknown"), _as_int(theme.get("count"))),
            )

    return {"run_id": run_id, "items_recorded": len(items), "db_path": str(path)}


def build_history_snapshot(path: Path, stale_after_days: int = 14) -> dict[str, Any]:
    if not path.exists():
        return _empty_snapshot(path)
    initialize_history_db(path)
    with _connect(path) as connection:
        run_count = _scalar(connection, "SELECT COUNT(*) FROM briefing_runs")
        signal_count = _scalar(connection, "SELECT COUNT(*) FROM signals")
        latest_run = _one(
            connection,
            """
            SELECT * FROM briefing_runs
            ORDER BY generated_at DESC, created_at DESC
            LIMIT 1
            """,
        )
        latest_run_id = latest_run["run_id"] if latest_run else None
        trend_rows = _with_run_deltas(
            _all(
                connection,
                """
                SELECT generated_at, item_count, reviewed_count, implement_count,
                       test_count, watch_count, archive_count, unreviewed_count,
                       top_theme, ROUND(avg_score, 1) AS avg_score
                FROM briefing_runs
                ORDER BY generated_at DESC, created_at DESC
                LIMIT 12
                """,
            )
        )
        decision_counts = _group_rows(connection, latest_run_id, "decision")
        source_counts = _source_rows(connection, latest_run_id)
        theme_counts = _theme_rows(connection, latest_run_id)
        open_actions = _open_action_rows(connection, latest_run_id)

    stale_actions = [
        row for row in open_actions if _age_days(row.get("recorded_at")) >= stale_after_days
    ]
    return {
        "has_database": True,
        "db_path": str(path),
        "run_count": run_count,
        "signal_count": signal_count,
        "latest_run": latest_run,
        "trend_rows": trend_rows,
        "decision_counts": decision_counts,
        "source_counts": source_counts,
        "theme_counts": theme_counts,
        "open_actions": open_actions,
        "stale_actions": stale_actions,
        "stale_after_days": stale_after_days,
    }


def build_weekly_summary(path: Path, limit: int = 8) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    initialize_history_db(path)
    with _connect(path) as connection:
        runs = _all(
            connection,
            """
            SELECT *
            FROM briefing_runs
            ORDER BY generated_at DESC, created_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        summaries: list[dict[str, Any]] = []
        for run in runs:
            run_id = str(run["run_id"])
            top_source = _one(
                connection,
                """
                SELECT source AS label, COUNT(*) AS count, ROUND(AVG(score), 1) AS avg_score
                FROM signals
                WHERE run_id = ?
                GROUP BY source
                ORDER BY count DESC, avg_score DESC, source ASC
                LIMIT 1
                """,
                (run_id,),
            )
            top_decision = _one(
                connection,
                """
                SELECT decision AS label, COUNT(*) AS count
                FROM signals
                WHERE run_id = ?
                GROUP BY decision
                ORDER BY count DESC, decision ASC
                LIMIT 1
                """,
                (run_id,),
            )
            open_action_count = _open_action_count(run)
            item_count = _as_int(run.get("item_count"))
            reviewed_count = _as_int(run.get("reviewed_count"))
            review_rate = _review_rate(run)
            top_theme = run.get("top_theme") or ""
            summaries.append(
                {
                    "generated_at": run["generated_at"],
                    "profile": run["profile"],
                    "signals": item_count,
                    "reviewed": reviewed_count,
                    "review_rate": review_rate,
                    "open_actions": open_action_count,
                    "implement": _as_int(run.get("implement_count")),
                    "test": _as_int(run.get("test_count")),
                    "watch": _as_int(run.get("watch_count")),
                    "archive": _as_int(run.get("archive_count")),
                    "unreviewed": _as_int(run.get("unreviewed_count")),
                    "avg_score": round(float(run.get("avg_score") or 0.0), 1),
                    "top_theme": top_theme,
                    "top_source": top_source["label"] if top_source else "",
                    "top_decision": top_decision["label"] if top_decision else "",
                    "stakeholder_summary": _stakeholder_summary(open_action_count, top_theme),
                }
            )
    return summaries


def build_trend_deltas(path: Path, limit: int = 8) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    initialize_history_db(path)
    with _connect(path) as connection:
        rows = _all(
            connection,
            """
            SELECT generated_at, item_count, reviewed_count, implement_count,
                   test_count, watch_count, archive_count, unreviewed_count,
                   top_theme, ROUND(avg_score, 1) AS avg_score
            FROM briefing_runs
            ORDER BY generated_at DESC, created_at DESC
            LIMIT ?
            """,
            (limit,),
        )
    return _with_run_deltas(rows)


def export_history_tables(path: Path, outdir: Path) -> dict[str, Path]:
    if not path.exists():
        return {}
    initialize_history_db(path)
    outdir.mkdir(parents=True, exist_ok=True)
    queries = {
        "runs": "SELECT * FROM briefing_runs ORDER BY generated_at DESC, created_at DESC",
        "signals": "SELECT * FROM signals ORDER BY recorded_at DESC, score DESC",
        "decision_counts": """
            SELECT run_id, decision, COUNT(*) AS count, ROUND(AVG(score), 1) AS avg_score
            FROM signals
            GROUP BY run_id, decision
            ORDER BY run_id, count DESC
        """,
        "source_counts": """
            SELECT run_id, source, COUNT(*) AS count, ROUND(AVG(score), 1) AS avg_score
            FROM signals
            GROUP BY run_id, source
            ORDER BY run_id, count DESC
        """,
        "themes": "SELECT * FROM theme_counts ORDER BY run_id, count DESC",
    }
    paths: dict[str, Path] = {}
    with _connect(path) as connection:
        for name, query in queries.items():
            rows = _all(connection, query)
            csv_path = outdir / f"signal_history_{name}.csv"
            _write_csv(csv_path, rows)
            paths[name] = csv_path

    weekly_summary_path = outdir / "ai_signal_weekly_summary.csv"
    _write_csv(weekly_summary_path, build_weekly_summary(path))
    paths["weekly_summary"] = weekly_summary_path

    trend_delta_path = outdir / "ai_signal_trend_deltas.csv"
    _write_csv(trend_delta_path, build_trend_deltas(path))
    paths["trend_deltas"] = trend_delta_path
    return paths


@contextmanager
def _connect(path: Path) -> Iterator[sqlite3.Connection]:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _run_id(profile: str, generated_at: str) -> str:
    key = f"{profile}|{generated_at}".encode("utf-8")
    return hashlib.sha1(key).hexdigest()[:12]


def _signal_key(item: dict[str, Any]) -> str:
    url = str(item.get("url") or "")
    canonical = canonicalize_url(url) if url else ""
    if canonical:
        return canonical
    title = str(item.get("title") or "untitled-signal").lower()
    return hashlib.sha1(title.encode("utf-8")).hexdigest()[:16]


def _memory_summary(payload: dict[str, Any], items: list[dict[str, Any]]) -> dict[str, int]:
    summary = payload.get("memory_summary")
    if isinstance(summary, dict):
        return {str(key): _as_int(value) for key, value in summary.items()}
    counts = {"unreviewed": 0, "watch": 0, "test": 0, "implement": 0, "archive": 0}
    for item in items:
        operator = item.get("operator") if isinstance(item.get("operator"), dict) else {}
        decision = str(operator.get("decision") or "unreviewed")
        counts[decision] = counts.get(decision, 0) + 1
    counts["reviewed"] = sum(value for key, value in counts.items() if key != "unreviewed")
    counts["total"] = len(items)
    return counts


def _average_score(items: list[dict[str, Any]]) -> float:
    if not items:
        return 0.0
    return round(sum(float(item.get("score") or 0.0) for item in items) / len(items), 2)


def _group_rows(connection: sqlite3.Connection, run_id: str | None, column: str) -> list[dict[str, Any]]:
    if not run_id:
        return []
    return _all(
        connection,
        f"SELECT {column} AS label, COUNT(*) AS count FROM signals WHERE run_id = ? GROUP BY {column} ORDER BY count DESC",
        (run_id,),
    )


def _source_rows(connection: sqlite3.Connection, run_id: str | None) -> list[dict[str, Any]]:
    if not run_id:
        return []
    return _all(
        connection,
        """
        SELECT source AS label, COUNT(*) AS count, ROUND(AVG(score), 1) AS avg_score
        FROM signals
        WHERE run_id = ?
        GROUP BY source
        ORDER BY count DESC, avg_score DESC
        LIMIT 10
        """,
        (run_id,),
    )


def _theme_rows(connection: sqlite3.Connection, run_id: str | None) -> list[dict[str, Any]]:
    if not run_id:
        return []
    return _all(
        connection,
        """
        SELECT theme AS label, count
        FROM theme_counts
        WHERE run_id = ?
        ORDER BY count DESC, theme ASC
        """,
        (run_id,),
    )


def _open_action_rows(connection: sqlite3.Connection, run_id: str | None) -> list[dict[str, Any]]:
    if not run_id:
        return []
    placeholders = ", ".join("?" for _ in ACTION_DECISIONS)
    return _all(
        connection,
        f"""
        SELECT title, url, source, decision, priority, linked_project,
               next_action, score, published_at, recorded_at
        FROM signals
        WHERE run_id = ? AND decision IN ({placeholders})
        ORDER BY score DESC
        LIMIT 20
        """,
        (run_id, *sorted(ACTION_DECISIONS)),
    )


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if rows:
        fieldnames = list(rows[0].keys())
    else:
        fieldnames = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        if rows:
            writer.writerows(rows)


def _all(
    connection: sqlite3.Connection,
    query: str,
    params: tuple[Any, ...] = (),
) -> list[dict[str, Any]]:
    return [dict(row) for row in connection.execute(query, params).fetchall()]


def _one(
    connection: sqlite3.Connection,
    query: str,
    params: tuple[Any, ...] = (),
) -> dict[str, Any] | None:
    row = connection.execute(query, params).fetchone()
    return dict(row) if row else None


def _scalar(
    connection: sqlite3.Connection,
    query: str,
    params: tuple[Any, ...] = (),
) -> int:
    return int(connection.execute(query, params).fetchone()[0])


def _empty_snapshot(path: Path) -> dict[str, Any]:
    return {
        "has_database": False,
        "db_path": str(path),
        "run_count": 0,
        "signal_count": 0,
        "latest_run": None,
        "trend_rows": [],
        "decision_counts": [],
        "source_counts": [],
        "theme_counts": [],
        "open_actions": [],
        "stale_actions": [],
        "stale_after_days": 14,
    }


def _with_run_deltas(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        current = dict(row)
        current_open_actions = _open_action_count(current)
        current["open_actions"] = current_open_actions
        current["review_rate"] = _review_rate(current)
        previous = rows[index + 1] if index + 1 < len(rows) else None
        if previous:
            previous_open_actions = _open_action_count(previous)
            current["open_actions_delta"] = current_open_actions - previous_open_actions
            current["avg_score_delta"] = round(
                float(current.get("avg_score") or 0.0) - float(previous.get("avg_score") or 0.0),
                1,
            )
            current["review_rate_delta"] = round(_review_rate(current) - _review_rate(previous), 3)
            current["comparison"] = "Compared with previous run"
        else:
            current["open_actions_delta"] = 0
            current["avg_score_delta"] = 0.0
            current["review_rate_delta"] = 0.0
            current["comparison"] = "No previous run"
        enriched.append(current)
    return enriched


def _open_action_count(row: dict[str, Any]) -> int:
    return _as_int(row.get("implement_count")) + _as_int(row.get("test_count")) + _as_int(row.get("watch_count"))


def _review_rate(row: dict[str, Any]) -> float:
    item_count = _as_int(row.get("item_count")) or _as_int(row.get("signals"))
    reviewed_count = _as_int(row.get("reviewed_count")) or _as_int(row.get("reviewed"))
    return round(reviewed_count / item_count, 3) if item_count else 0.0


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _age_days(value: str | None) -> float:
    if not value:
        return 0.0
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return 0.0
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return max((datetime.now(timezone.utc) - parsed.astimezone(timezone.utc)).total_seconds() / 86400, 0.0)


def _stakeholder_summary(open_actions: int, top_theme: str) -> str:
    if open_actions and top_theme:
        return f"{open_actions} open actions led by {top_theme}."
    if open_actions:
        return f"{open_actions} open actions need review."
    if top_theme:
        return f"No open actions; strongest theme was {top_theme}."
    return "No open actions or dominant theme recorded."


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
