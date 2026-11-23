#!/usr/bin/env python3
"""Download the official MCP Registry into a local SQLite full-text index.

Why: the registry's own search only matches a substring of the server *name*.
A local FTS5 index lets us search names AND descriptions, with OR-ed synonyms
and BM25 ranking.

Usage:
    python3 build_index.py            # full crawl the first time, incremental afterwards
    python3 build_index.py --full     # force a full re-crawl
    python3 build_index.py --status   # print index size and last update

Index location: ~/.cache/tool-finder/catalog.db
"""
import argparse
import datetime as dt
import json
import os
import sqlite3
import subprocess
import sys
import urllib.parse

DB = os.path.expanduser("~/.cache/tool-finder/catalog.db")
BASE = "https://registry.modelcontextprotocol.io/v0/servers"


def fetch(params):
    url = BASE + "?" + urllib.parse.urlencode(params)
    p = subprocess.run(["curl", "-sS", "--fail", "-m", "30", "--retry", "3", url],
                       capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.strip())
    return json.loads(p.stdout)


def connect():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    db = sqlite3.connect(DB)
    db.executescript("""
    CREATE TABLE IF NOT EXISTS mcp (
        name TEXT PRIMARY KEY, title TEXT, description TEXT, repo TEXT,
        packages TEXT, remotes TEXT, version TEXT, updated TEXT, status TEXT);
    CREATE VIRTUAL TABLE IF NOT EXISTS mcp_fts USING fts5(
        name, title, description, content='mcp', content_rowid='rowid',
        tokenize='porter unicode61');
    CREATE TRIGGER IF NOT EXISTS mcp_ai AFTER INSERT ON mcp BEGIN
        INSERT INTO mcp_fts(rowid, name, title, description) VALUES (new.rowid, new.name, new.title, new.description); END;
    CREATE TRIGGER IF NOT EXISTS mcp_ad AFTER DELETE ON mcp BEGIN
        INSERT INTO mcp_fts(mcp_fts, rowid, name, title, description) VALUES ('delete', old.rowid, old.name, old.title, old.description); END;
    CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT);
    """)
    return db


def upsert(db, item):
    s = item.get("server", {})
    m = item.get("_meta", {}).get("io.modelcontextprotocol.registry/official", {})
    name = s.get("name")
    if not name:
        return
    db.execute("DELETE FROM mcp WHERE name = ?", (name,))
    db.execute(
        "INSERT INTO mcp VALUES (?,?,?,?,?,?,?,?,?)",
        (
            name,
            s.get("title") or "",
            s.get("description") or "",
            (s.get("repository") or {}).get("url") or "",
            json.dumps([f"{p.get('registryType')}:{p.get('identifier')}" for p in s.get("packages") or []]),
            json.dumps([r.get("type") for r in s.get("remotes") or []]),
            s.get("version") or "",
            (m.get("updatedAt") or "")[:19],
            m.get("status") or "",
        ),
    )


def crawl(db, since=None):
    params = {"limit": 100, "version": "latest"}
    if since:
        params["updated_since"] = since
    cursor, n = None, 0
    while True:
        if cursor:
            params["cursor"] = cursor
        data = fetch(params)
        for item in data.get("servers", []):
            upsert(db, item)
            n += 1
        db.commit()
        cursor = (data.get("metadata") or {}).get("nextCursor")
        print(f"\r  {n} servers…", end="", file=sys.stderr, flush=True)
        if not cursor or not data.get("servers"):
            break
    print(file=sys.stderr)
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--status", action="store_true")
    a = ap.parse_args()
    db = connect()
    last = (db.execute("SELECT v FROM meta WHERE k='mcp_updated'").fetchone() or [None])[0]
    if a.status:
        count = db.execute("SELECT count(*) FROM mcp").fetchone()[0]
        print(json.dumps({"db": DB, "mcp_servers": count, "last_crawl": last}))
        return
    started = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    since = None if (a.full or not last) else last
    print(f"crawling MCP registry ({'incremental since ' + since if since else 'full'})", file=sys.stderr)
    n = crawl(db, since)
    db.execute("INSERT OR REPLACE INTO meta VALUES ('mcp_updated', ?)", (started,))
    db.commit()
    total = db.execute("SELECT count(*) FROM mcp").fetchone()[0]
    print(json.dumps({"fetched": n, "mcp_servers": total, "db": DB}))


if __name__ == "__main__":
    main()
