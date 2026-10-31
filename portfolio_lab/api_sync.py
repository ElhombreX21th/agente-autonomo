"""Resumable, idempotent JSON API sync with durable SQLite cursor.

Demonstration uses synthetic mock pages. No external URL or secrets needed.
"""
import json
import sqlite3
from typing import Callable
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen


def connect(database_path: str = ":memory:") -> sqlite3.Connection:
    conn = sqlite3.connect(database_path)
    conn.execute("""CREATE TABLE IF NOT EXISTS records (
        id TEXT PRIMARY KEY, updated_at TEXT NOT NULL, payload TEXT NOT NULL
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS sync_state (
        name TEXT PRIMARY KEY, cursor TEXT
    )""")
    conn.commit()
    return conn


def current_cursor(conn: sqlite3.Connection, name: str = "demo") -> str | None:
    row = conn.execute("SELECT cursor FROM sync_state WHERE name=?", (name,)).fetchone()
    return row[0] if row else None


def sync_pages(conn: sqlite3.Connection, fetch_page: Callable[[str | None], dict],
               name: str = "demo", max_pages: int = 100) -> dict:
    """One transaction per page: page records and its cursor commit atomically."""
    if max_pages < 1:
        raise ValueError("max_pages must be >= 1")
    cursor = current_cursor(conn, name)
    seen_cursors = set()
    processed = 0
    pages = 0
    while pages < max_pages:
        if cursor in seen_cursors:
            raise ValueError("Cursor cycle detected")
        seen_cursors.add(cursor)
        response = fetch_page(cursor)
        if not isinstance(response, dict) or not isinstance(response.get("items"), list):
            raise ValueError("API page must contain an items list")
        next_cursor = response.get("next_cursor")
        if next_cursor is not None and (not isinstance(next_cursor, str) or not next_cursor):
            raise ValueError("Invalid next_cursor")
        if next_cursor == cursor and cursor is not None:
            raise ValueError("API repeated the same cursor")
        validated = []
        for item in response["items"]:
            if not isinstance(item, dict) or not all(
                isinstance(item.get(key), str) and item[key].strip()
                for key in ("id", "updated_at")
            ):
                raise ValueError("Each item needs nonempty id and updated_at strings")
            validated.append((item["id"], item["updated_at"], json.dumps(item, sort_keys=True)))
        with conn:
            conn.executemany("""INSERT INTO records (id, updated_at, payload)
                VALUES (?, ?, ?) ON CONFLICT(id) DO UPDATE SET
                updated_at=excluded.updated_at, payload=excluded.payload
                WHERE excluded.updated_at >= records.updated_at""", validated)
            conn.execute("INSERT INTO sync_state(name,cursor) VALUES(?,?) "
                         "ON CONFLICT(name) DO UPDATE SET cursor=excluded.cursor",
                         (name, next_cursor))
        processed += len(validated)
        pages += 1
        cursor = next_cursor
        if cursor is None:
            break
    return {"pages_processed": pages, "records_seen": processed,
            "unique_records_in_db": conn.execute("SELECT COUNT(*) FROM records").fetchone()[0],
            "next_cursor": cursor, "finished": cursor is None}


def http_json_page_fetcher(url: str, token: str | None = None,
                           timeout: int = 8) -> Callable[[str | None], dict]:
    """Opt-in HTTP(S) adapter; only call with endpoints you are authorized to use."""
    parts = urlsplit(url)
    if parts.scheme not in {"https", "http"} or not parts.netloc:
        raise ValueError("An absolute HTTP(S) endpoint is required")
    if parts.scheme == "http" and parts.hostname not in {"127.0.0.1", "localhost"}:
        raise ValueError("Use HTTPS for non-local APIs")
    if timeout <= 0:
        raise ValueError("Timeout must be positive")

    def fetch(cursor: str | None) -> dict:
        query = urlencode({"cursor": cursor}) if cursor else ""
        separator = "&" if "?" in url else "?"
        endpoint = url + (separator + query if query else "")
        headers = {"Accept": "application/json", "User-Agent": "PortfolioLab/1.0"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        req = Request(endpoint, headers=headers)
        with urlopen(req, timeout=timeout) as response:
            if response.status != 200:
                raise ValueError("Unexpected API response status")
            return json.loads(response.read(1_000_000).decode("utf-8"))

    return fetch
