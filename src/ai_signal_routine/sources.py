from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote_plus

import requests

from .models import SignalItem
from .utils import clean_text, parse_datetime


ATOM_NS = "{http://www.w3.org/2005/Atom}"


@dataclass(slots=True)
class FetchResult:
    items: list[SignalItem]
    errors: list[str]


class SourceCollector:
    def __init__(self, timeout: int = 20) -> None:
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "ai-signal-routine/0.1 (+https://example.local)",
                "Accept": "application/json, application/xml, text/xml, text/html;q=0.8, */*;q=0.5",
            }
        )

    def fetch_all(self, config: dict[str, Any]) -> FetchResult:
        items: list[SignalItem] = []
        errors: list[str] = []
        per_source_limit = config["limits"]["per_source"]
        for source in config["sources"]:
            try:
                fetched = self.fetch_source(source, per_source_limit)
                items.extend(fetched)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{source['name']}: {exc}")
        return FetchResult(items=items, errors=errors)

    def fetch_source(self, source: dict[str, Any], limit: int) -> list[SignalItem]:
        source_type = source["type"]
        if source_type == "rss":
            return self._fetch_rss(source, limit)
        if source_type == "hn_algolia":
            return self._fetch_hn(source, limit)
        if source_type == "github_search":
            return self._fetch_github(source, limit)
        if source_type == "github_watchlist":
            return self._fetch_github_watchlist(source)
        if source_type == "arxiv":
            return self._fetch_arxiv(source, limit)
        raise ValueError(f"Unsupported source type: {source_type}")

    def _request_json(self, url: str, headers: dict[str, str] | None = None) -> Any:
        response = self.session.get(url, timeout=self.timeout, headers=headers)
        response.raise_for_status()
        return response.json()

    def _request_text(self, url: str) -> str:
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.text

    def _fetch_rss(self, source: dict[str, Any], limit: int) -> list[SignalItem]:
        body = self._request_text(source["url"])
        root = ET.fromstring(body)
        items: list[SignalItem] = []

        if root.tag.endswith("rss"):
            channel = root.find("channel")
            if channel is None:
                return items
            for entry in channel.findall("item")[:limit]:
                title = clean_text(self._text(entry, "title"))
                url = clean_text(self._text(entry, "link"))
                summary = clean_text(
                    self._text(entry, "description")
                    or self._text(entry, "{http://purl.org/rss/1.0/modules/content/}encoded")
                )
                published_at = parse_datetime(
                    self._text(entry, "pubDate") or self._text(entry, "date")
                )
                if not title or not url:
                    continue
                items.append(
                    SignalItem(
                        title=title,
                        url=url,
                        source=source["name"],
                        group=source["group"],
                        source_type=source["type"],
                        published_at=published_at,
                        summary=summary,
                        tags=list(source.get("tags", [])),
                    )
                )
            return items

        if root.tag.endswith("feed"):
            for entry in root.findall(f"{ATOM_NS}entry")[:limit]:
                title = clean_text(self._text(entry, f"{ATOM_NS}title"))
                url = self._atom_link(entry)
                summary = clean_text(
                    self._text(entry, f"{ATOM_NS}summary")
                    or self._text(entry, f"{ATOM_NS}content")
                )
                published_at = parse_datetime(
                    self._text(entry, f"{ATOM_NS}published")
                    or self._text(entry, f"{ATOM_NS}updated")
                )
                if not title or not url:
                    continue
                items.append(
                    SignalItem(
                        title=title,
                        url=url,
                        source=source["name"],
                        group=source["group"],
                        source_type=source["type"],
                        published_at=published_at,
                        summary=summary,
                        tags=list(source.get("tags", [])),
                    )
                )
        return items

    def _fetch_hn(self, source: dict[str, Any], limit: int) -> list[SignalItem]:
        items: list[SignalItem] = []
        max_hits = source.get("hits_per_query", 5)
        for query in source["queries"]:
            url = (
                "https://hn.algolia.com/api/v1/search_by_date"
                f"?query={quote_plus(query)}&tags=story&hitsPerPage={max_hits}"
            )
            payload = self._request_json(url)
            for hit in payload.get("hits", []):
                story_url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit['objectID']}"
                title = clean_text(hit.get("title") or hit.get("story_title"))
                if not title or not story_url:
                    continue
                items.append(
                    SignalItem(
                        title=title,
                        url=story_url,
                        source=source["name"],
                        group=source["group"],
                        source_type=source["type"],
                        published_at=parse_datetime(hit.get("created_at")),
                        summary=clean_text(hit.get("story_text") or ""),
                        tags=list(source.get("tags", [])) + [query.lower()],
                        metadata={"points": hit.get("points"), "query": query},
                    )
                )
        return self._sort_recent(items)[:limit * max(len(source["queries"]), 1)]

    def _fetch_github(self, source: dict[str, Any], limit: int) -> list[SignalItem]:
        items: list[SignalItem] = []
        token = None
        headers: dict[str, str] = {"Accept": "application/vnd.github+json"}
        try:
            import os

            token = os.environ.get("GITHUB_TOKEN")
        except Exception:  # noqa: BLE001
            token = None
        if token:
            headers["Authorization"] = f"Bearer {token}"

        per_query = source.get("per_query", 5)
        for query in source["queries"]:
            q = query["query"]
            sort = query.get("sort", "stars")
            url = (
                "https://api.github.com/search/repositories"
                f"?q={quote_plus(q)}&sort={quote_plus(sort)}&order=desc&per_page={per_query}"
            )
            payload = self._request_json(url, headers=headers)
            for repo in payload.get("items", []):
                description = clean_text(repo.get("description"))
                stars = int(repo.get("stargazers_count", 0))
                updated_at = parse_datetime(repo.get("updated_at"))
                summary = description
                if summary:
                    summary = f"{summary} Stars: {stars:,}. Language: {repo.get('language') or 'Unknown'}."
                items.append(
                    SignalItem(
                        title=repo["full_name"],
                        url=repo["html_url"],
                        source=source["name"],
                        group=source["group"],
                        source_type=source["type"],
                        published_at=updated_at,
                        summary=summary,
                        tags=list(source.get("tags", [])) + list(repo.get("topics", [])),
                        metadata={
                            "stars": stars,
                            "forks": repo.get("forks_count", 0),
                            "language": repo.get("language"),
                            "query": q,
                            "updated_at": repo.get("updated_at"),
                        },
                    )
                )
        return self._sort_recent(items)[:limit * max(len(source["queries"]), 1)]

    def _fetch_arxiv(self, source: dict[str, Any], limit: int) -> list[SignalItem]:
        items: list[SignalItem] = []
        per_query = source.get("per_query", 4)
        for query in source["queries"]:
            url = (
                "https://export.arxiv.org/api/query"
                f"?search_query={quote_plus(query)}&start=0&max_results={per_query}"
                "&sortBy=lastUpdatedDate&sortOrder=descending"
            )
            body = self._request_text(url)
            root = ET.fromstring(body)
            for entry in root.findall(f"{ATOM_NS}entry"):
                title = clean_text(self._text(entry, f"{ATOM_NS}title"))
                summary = clean_text(self._text(entry, f"{ATOM_NS}summary"))
                url = self._atom_link(entry) or clean_text(self._text(entry, f"{ATOM_NS}id"))
                published_at = parse_datetime(
                    self._text(entry, f"{ATOM_NS}updated")
                    or self._text(entry, f"{ATOM_NS}published")
                )
                categories = [
                    clean_text(cat.attrib.get("term"))
                    for cat in entry.findall(f"{ATOM_NS}category")
                    if cat.attrib.get("term")
                ]
                if not title or not url:
                    continue
                items.append(
                    SignalItem(
                        title=title,
                        url=url,
                        source=source["name"],
                        group=source["group"],
                        source_type=source["type"],
                        published_at=published_at,
                        summary=summary,
                        tags=list(source.get("tags", [])) + categories,
                        metadata={"query": query},
                    )
                )
        return self._sort_recent(items)[:limit * max(len(source["queries"]), 1)]

    def _fetch_github_watchlist(self, source: dict[str, Any]) -> list[SignalItem]:
        items: list[SignalItem] = []
        token = None
        headers: dict[str, str] = {"Accept": "application/vnd.github+json"}
        try:
            import os

            token = os.environ.get("GITHUB_TOKEN")
        except Exception:  # noqa: BLE001
            token = None
        if token:
            headers["Authorization"] = f"Bearer {token}"

        for repo_name in source["repos"]:
            url = f"https://api.github.com/repos/{repo_name}"
            repo = self._request_json(url, headers=headers)
            description = clean_text(repo.get("description"))
            stars = int(repo.get("stargazers_count", 0))
            summary = description
            if summary:
                summary = f"{summary} Stars: {stars:,}. Language: {repo.get('language') or 'Unknown'}."
            items.append(
                SignalItem(
                    title=repo["full_name"],
                    url=repo["html_url"],
                    source=source["name"],
                    group=source["group"],
                    source_type=source["type"],
                    published_at=parse_datetime(repo.get("updated_at")),
                    summary=summary,
                    tags=list(source.get("tags", [])) + list(repo.get("topics", [])),
                    metadata={
                        "stars": stars,
                        "forks": repo.get("forks_count", 0),
                        "language": repo.get("language"),
                        "updated_at": repo.get("updated_at"),
                        "watchlist": True,
                    },
                )
            )
        return self._sort_recent(items)

    @staticmethod
    def _atom_link(entry: ET.Element) -> str:
        for link in entry.findall(f"{ATOM_NS}link"):
            href = link.attrib.get("href")
            rel = link.attrib.get("rel", "alternate")
            if href and rel == "alternate":
                return href
        fallback = entry.find(f"{ATOM_NS}id")
        return clean_text(fallback.text if fallback is not None else "")

    @staticmethod
    def _text(parent: ET.Element, tag: str) -> str:
        child = parent.find(tag)
        if child is None or child.text is None:
            return ""
        return child.text

    @staticmethod
    def _sort_recent(items: list[SignalItem]) -> list[SignalItem]:
        fallback = datetime(1970, 1, 1, tzinfo=timezone.utc)
        return sorted(items, key=lambda item: item.published_at or fallback, reverse=True)
