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
        self.errors: list[str] = []
        self.github_auth_disabled = False
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
        self.errors = []
        self.github_auth_disabled = False
        per_source_limit = config["limits"]["per_source"]
        for source in config["sources"]:
            try:
                fetched = self.fetch_source(source, per_source_limit)
                items.extend(fetched)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{source['name']}: {exc}")
        errors.extend(self.errors)
        return FetchResult(items=items, errors=errors)

    def fetch_source(self, source: dict[str, Any], limit: int) -> list[SignalItem]:
        source_type = source["type"]
        if source_type == "rss":
            return self._fetch_rss(source, limit)
        if source_type == "hn_algolia":
            return self._fetch_hn(source, limit)
        if source_type == "reddit_search":
            return self._fetch_reddit(source, limit)
        if source_type == "github_search":
            return self._fetch_github(source, limit)
        if source_type == "github_watchlist":
            return self._fetch_github_watchlist(source)
        if source_type == "github_releases_watchlist":
            return self._fetch_github_releases_watchlist(source)
        if source_type == "arxiv":
            return self._fetch_arxiv(source, limit)
        raise ValueError(f"Unsupported source type: {source_type}")

    def _request_json(self, url: str, headers: dict[str, str] | None = None) -> Any:
        response = self.session.get(url, timeout=self.timeout, headers=headers)
        response.raise_for_status()
        return response.json()

    def _request_github_json(self, url: str, headers: dict[str, str], source_name: str) -> Any:
        try:
            return self._request_json(url, headers=headers)
        except requests.HTTPError as exc:
            response = exc.response
            if response is not None and response.status_code == 401 and "Authorization" in headers:
                self.github_auth_disabled = True
                self._record_error(
                    source_name,
                    "`GITHUB_TOKEN` was rejected. Falling back to unauthenticated GitHub API.",
                )
                headers.pop("Authorization", None)
                fallback_headers = dict(headers)
                return self._request_json(url, headers=fallback_headers)
            raise

    def _request_text(self, url: str) -> str:
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.text

    def _record_error(self, source_name: str, detail: str) -> None:
        message = f"{source_name}: {detail}"
        if message not in self.errors:
            self.errors.append(message)

    @staticmethod
    def _is_rate_limit_error(exc: Exception) -> bool:
        if isinstance(exc, requests.HTTPError) and exc.response is not None:
            response = exc.response
            if response.status_code == 429:
                return True
            if response.status_code == 403:
                if response.headers.get("X-RateLimit-Remaining") == "0":
                    return True
                try:
                    message = str(response.json().get("message", "")).lower()
                except (requests.JSONDecodeError, ValueError):
                    message = response.text.lower()
                if "rate limit" in message or "secondary rate limit" in message:
                    return True
        text = str(exc).lower()
        return "rate limit" in text or "429" in text

    @staticmethod
    def _is_timeout_error(exc: Exception) -> bool:
        return "timed out" in str(exc).lower()

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
            try:
                payload = self._request_json(url)
            except requests.RequestException as exc:
                self._record_error(source["name"], f"{query}: {exc}")
                continue
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

    def _fetch_reddit(self, source: dict[str, Any], limit: int) -> list[SignalItem]:
        items: list[SignalItem] = []
        hits_per_query = source.get("hits_per_query", 2)
        sort = source.get("sort", "new")
        time_window = source.get("time", "week")
        subreddits = source.get("subreddits", [])
        queries = source.get("queries", [])

        for subreddit in subreddits:
            for query in queries:
                url = (
                    f"https://www.reddit.com/r/{quote_plus(subreddit)}/search.json"
                    f"?q={quote_plus(query)}&restrict_sr=1&sort={quote_plus(sort)}"
                    f"&t={quote_plus(time_window)}&limit={hits_per_query}&raw_json=1"
                )
                try:
                    payload = self._request_json(url)
                except requests.RequestException as exc:
                    self._record_error(source["name"], f"r/{subreddit} {query}: {exc}")
                    continue
                for child in payload.get("data", {}).get("children", []):
                    post = child.get("data", {})
                    title = clean_text(post.get("title"))
                    permalink = post.get("permalink")
                    url_value = (
                        f"https://www.reddit.com{permalink}"
                        if permalink
                        else clean_text(post.get("url_overridden_by_dest") or post.get("url"))
                    )
                    if not title or not url_value:
                        continue
                    created_utc = post.get("created_utc")
                    published_at = None
                    if isinstance(created_utc, (int, float)):
                        published_at = datetime.fromtimestamp(created_utc, tz=timezone.utc)
                    summary = clean_text(
                        post.get("selftext")
                        or post.get("url_overridden_by_dest")
                        or post.get("url")
                    )
                    items.append(
                        SignalItem(
                            title=title,
                            url=url_value,
                            source=source["name"],
                            group=source["group"],
                            source_type=source["type"],
                            published_at=published_at,
                            summary=summary,
                            tags=list(source.get("tags", [])) + [subreddit.lower(), query.lower()],
                            metadata={
                                "query": query,
                                "subreddit": subreddit,
                                "points": post.get("score", 0),
                                "comments": post.get("num_comments", 0),
                            },
                        )
                    )
        return self._sort_recent(items)[:limit * max(len(subreddits), 1)]

    def _fetch_github(self, source: dict[str, Any], limit: int) -> list[SignalItem]:
        items: list[SignalItem] = []
        headers = self._github_headers()

        per_query = source.get("per_query", 5)
        for query in source["queries"]:
            q = query["query"]
            sort = query.get("sort", "stars")
            url = (
                "https://api.github.com/search/repositories"
                f"?q={quote_plus(q)}&sort={quote_plus(sort)}&order=desc&per_page={per_query}"
            )
            try:
                payload = self._request_github_json(url, headers, source["name"])
            except requests.RequestException as exc:
                if self._is_rate_limit_error(exc):
                    self._record_error(
                        source["name"],
                        "GitHub API rate limit reached. Set `GITHUB_TOKEN` for higher daily coverage.",
                    )
                    break
                self._record_error(source["name"], f"{q}: {exc}")
                continue
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
            try:
                body = self._request_text(url)
            except requests.RequestException as exc:
                if self._is_rate_limit_error(exc) or self._is_timeout_error(exc):
                    self._record_error(
                        source["name"],
                        "arXiv was rate-limited or timed out. Research radar will retry on the next run.",
                    )
                    break
                self._record_error(source["name"], f"{query}: {exc}")
                continue
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
        headers = self._github_headers()

        for repo_name in source["repos"]:
            url = f"https://api.github.com/repos/{repo_name}"
            try:
                repo = self._request_github_json(url, headers, source["name"])
            except requests.RequestException as exc:
                if self._is_rate_limit_error(exc):
                    self._record_error(
                        source["name"],
                        "GitHub API rate limit reached. Set `GITHUB_TOKEN` for full watchlist coverage.",
                    )
                    break
                self._record_error(source["name"], f"{repo_name}: {exc}")
                continue
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

    def _fetch_github_releases_watchlist(self, source: dict[str, Any]) -> list[SignalItem]:
        items: list[SignalItem] = []
        headers = self._github_headers()
        per_repo = source.get("per_repo", 1)

        for repo_name in source["repos"]:
            try:
                repo = self._request_github_json(
                    f"https://api.github.com/repos/{repo_name}", headers, source["name"]
                )
                releases = self._request_github_json(
                    f"https://api.github.com/repos/{repo_name}/releases?per_page={per_repo}",
                    headers,
                    source["name"],
                )
            except requests.RequestException as exc:
                if self._is_rate_limit_error(exc):
                    self._record_error(
                        source["name"],
                        "GitHub API rate limit reached. Set `GITHUB_TOKEN` for full release coverage.",
                    )
                    break
                self._record_error(source["name"], f"{repo_name}: {exc}")
                continue
            if not isinstance(releases, list):
                continue

            for release in releases:
                if release.get("draft"):
                    continue
                title = clean_text(
                    release.get("name") or f"{repo_name} {release.get('tag_name') or 'release'}"
                )
                body = clean_text(release.get("body") or "")
                if body:
                    summary = (
                        f"Release {release.get('tag_name') or 'update'} for {repo_name}. "
                        f"{_truncate_text(body, 220)}"
                    )
                else:
                    summary = f"Release {release.get('tag_name') or 'update'} for {repo_name}."
                items.append(
                    SignalItem(
                        title=title,
                        url=release.get("html_url") or repo.get("html_url"),
                        source=source["name"],
                        group=source["group"],
                        source_type=source["type"],
                        published_at=parse_datetime(release.get("published_at") or release.get("created_at")),
                        summary=summary,
                        tags=list(source.get("tags", [])) + list(repo.get("topics", [])),
                        metadata={
                            "repo": repo_name,
                            "stars": int(repo.get("stargazers_count", 0)),
                            "forks": repo.get("forks_count", 0),
                            "language": repo.get("language"),
                            "updated_at": repo.get("updated_at"),
                            "release_tag": release.get("tag_name"),
                            "release_name": release.get("name"),
                            "release_watchlist": True,
                        },
                    )
                )
        return self._sort_recent(items)

    def _github_headers(self) -> dict[str, str]:
        token = None
        headers: dict[str, str] = {"Accept": "application/vnd.github+json"}
        try:
            import os

            token = os.environ.get("GITHUB_TOKEN", "").strip().strip('"').strip("'")
        except Exception:  # noqa: BLE001
            token = None
        if token and not self.github_auth_disabled:
            headers["Authorization"] = f"Bearer {token}"
        return headers

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


def _truncate_text(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[: limit - 3].rstrip() + "..."
