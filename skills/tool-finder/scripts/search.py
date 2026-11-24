#!/usr/bin/env python3
"""Search several AI-tool directories in parallel and print one normalized JSON result.

Usage:
    python3 search.py "gmail draft" "email reply" [--limit 8] [--sources mcp,skill,workflow,github,plugin]

Each positional argument is one English keyword query. Every query is sent to every
selected source at the same time; results are de-duplicated per source.

Sources:
    mcp       Official MCP Registry (registry.modelcontextprotocol.io)
    skill     skills.sh directory (agent skills, with install counts)
    workflow  n8n workflow templates (api.n8n.io)
    github    GitHub repositories (stars, last push) - agents, bots, plugins, MCP servers
    plugin    Claude Code plugin marketplaces on GitHub (.claude-plugin/marketplace.json)

Uses only the Python standard library. If the `gh` CLI is logged in, its token is used
for GitHub calls (higher rate limit, and required for the `plugin` source).
"""
import argparse
import datetime as dt
import json
import os
import re
import sqlite3
import subprocess
import sys
import urllib.parse
import threading
import time
from concurrent.futures import ThreadPoolExecutor

UA = "tool-finder-skill/1.0"
TIMEOUT = 20


RETRY_STATUS = {429, 403, 502, 503}
# Per-source concurrency caps: GitHub search allows ~30 req/min, code search ~10 req/min,
# skills.sh (Algolia) throttles bursts. Parallel tool-finder runs hit these limits in iteration-1.
SOURCE_SLOTS = {"github": 2, "plugin": 1, "skill": 3}
_SEMS = {}


def _get(url, headers=None, retries=2):
    # Use system curl: python.org builds on macOS often lack CA certificates, curl doesn't.
    # Headers go through stdin (-K -) so a GitHub token never appears in the process list.
    config = "".join(f'header = "{k}: {v}"\n' for k, v in {"User-Agent": UA, **(headers or {})}.items())
    for attempt in range(retries + 1):
        proc = subprocess.run(
            ["curl", "-sS", "-m", str(TIMEOUT), "-w", "\n%{http_code}", "-K", "-", url],
            input=config, capture_output=True, text=True,
        )
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip() or f"curl exit {proc.returncode}")
        body, _, code = proc.stdout.rpartition("\n")
        status = int(code or 0)
        if 200 <= status < 300:
            return json.loads(body)
        if status in RETRY_STATUS and attempt < retries:
            time.sleep(4 * (attempt + 1))  # 4s, 8s: enough for a per-minute window to loosen
            continue
        raise RuntimeError(f"HTTP {status}")


def _limited(src, fn):
    sem = _SEMS.setdefault(src, threading.Semaphore(SOURCE_SLOTS.get(src, 12)))

    def run(q, limit):
        with sem:
            return fn(q, limit)
    return run


def _gh_token():
    # Prefer a dedicated fine-grained, read-only, public-repos-only token if the user set one.
    # Falls back to the gh CLI token (broader scopes; only ever sent to api.github.com).
    if os.environ.get("TOOL_FINDER_GH_TOKEN"):
        return os.environ["TOOL_FINDER_GH_TOKEN"]
    try:
        out = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, timeout=10)
        return out.stdout.strip() or None
    except Exception:
        return None


GH_TOKEN = None


def _gh_headers():
    h = {"Accept": "application/vnd.github+json"}
    if GH_TOKEN:
        h["Authorization"] = f"Bearer {GH_TOKEN}"
    return h


def _short(text, n=180):
    text = " ".join((text or "").split())
    return text if len(text) <= n else text[: n - 1] + "…"


def _per_month(stars, created):
    """Momentum signal: stars divided by months since creation (min 1 month)."""
    try:
        c = dt.datetime.fromisoformat(created.replace("Z", "+00:00"))
        months = max(1.0, (dt.datetime.now(dt.timezone.utc) - c).days / 30.4)
        return round((stars or 0) / months, 1)
    except Exception:
        return None


# ---------------------------------------------------------------- sources

INDEX_DB = os.path.expanduser("~/.cache/tool-finder/catalog.db")


def search_mcp(q, limit):
    """Prefer the local full-text index (name + description); fall back to the live API."""
    if os.path.exists(INDEX_DB):
        try:
            res = search_mcp_local(q, limit)
            if res is not None:
                return res
        except sqlite3.Error:
            pass
    return search_mcp_api(q, limit)


def search_mcp_local(q, limit):
    words = [w for w in re.findall(r"[A-Za-z0-9]+", q) if len(w) >= 2]
    if not words:
        return []
    db = sqlite3.connect(f"file:{INDEX_DB}?mode=ro", uri=True)
    if db.execute("SELECT count(*) FROM mcp").fetchone()[0] == 0:
        return None
    sql = """SELECT m.name, m.title, m.description, m.repo, m.packages, m.remotes, m.updated,
                    bm25(mcp_fts, 5.0, 3.0, 1.0) AS score
             FROM mcp_fts JOIN mcp m ON m.rowid = mcp_fts.rowid
             WHERE mcp_fts MATCH ? AND m.status IN ('', 'active')
             ORDER BY score LIMIT ?"""
    # every word must match (prefix) first; if that is too strict, accept any word
    rows = db.execute(sql, (" AND ".join(f'"{w}"*' for w in words), limit)).fetchall()
    mode = "all-words"
    if len(rows) < max(3, limit // 2) and len(words) > 1:
        seen = {r[0] for r in rows}
        extra = db.execute(sql, (" OR ".join(f'"{w}"*' for w in words), limit * 2)).fetchall()
        rows += [r for r in extra if r[0] not in seen][: limit - len(rows)]
        mode = "all-words+any-word"
    out = []
    for name, title, desc, repo, pk, rm, upd, score in rows:
        out.append({
            "name": name,
            "title": title or None,
            "description": _short(desc),
            "url": repo or "https://registry.modelcontextprotocol.io/v0/servers?" + urllib.parse.urlencode({"search": name}),
            "install": {"packages": json.loads(pk or "[]"), "remote": json.loads(rm or "[]")},
            "updated": (upd or "")[:10],
            "via": f"local-index ({mode})",
        })
    return out


def search_mcp_api(q, limit):
    # The registry only matches a single substring against the server *name*,
    # so a multi-word query returns nothing. Query each word separately, then rank
    # by how many of the query words appear in name + description.
    words = [w.lower() for w in q.split() if len(w) >= 3] or [q.lower()]
    seen = {}
    for w in words:
        url = "https://registry.modelcontextprotocol.io/v0/servers?" + urllib.parse.urlencode(
            {"search": w, "limit": 100}
        )
        for item in _get(url).get("servers", []):
            s = item.get("server", {})
            meta = item.get("_meta", {}).get("io.modelcontextprotocol.registry/official", {})
            if meta.get("isLatest") is False or meta.get("status") not in (None, "active"):
                continue
            name = s.get("name")
            if name in seen:
                continue
            hay = f"{name} {s.get('description') or ''}".lower()
            repo = (s.get("repository") or {}).get("url")
            seen[name] = {
                "name": name,
                "description": _short(s.get("description")),
                "url": repo or "https://registry.modelcontextprotocol.io/v0/servers?"
                + urllib.parse.urlencode({"search": name}),
                "install": {
                    "packages": [f"{p.get('registryType')}:{p.get('identifier')}" for p in s.get("packages") or []],
                    "remote": [r.get("type") for r in s.get("remotes") or []],
                },
                "updated": (meta.get("updatedAt") or "")[:10],
                "_score": sum(1 for x in words if re.search(r"(?<![a-z0-9])" + re.escape(x), hay)),
            }
    ranked = sorted(seen.values(), key=lambda x: (x["_score"], x["updated"]), reverse=True)
    out = []
    for it in [r for r in ranked if r["_score"] > 0][:limit]:
        it["word_matches"] = f"{it.pop('_score')}/{len(words)}"
        it["via"] = "live-api (name-only search; run build_index.py for description search)"
        out.append(it)
    return out


def search_skill(q, limit):
    data = _get("https://skills.sh/api/search?" + urllib.parse.urlencode({"q": q}))
    out = []
    for s in data.get("skills", [])[:limit]:
        out.append({
            "name": s.get("name"),
            "source_repo": s.get("source"),
            "url": f"https://skills.sh/{s.get('id')}",
            "github": f"https://github.com/{s.get('source')}",
            "installs": s.get("installs"),
            "install": f"npx skills add {s.get('source')} --skill {s.get('skillId')}",
        })
    return out


def search_workflow(q, limit):
    data = _get("https://api.n8n.io/api/templates/search?" + urllib.parse.urlencode({"search": q, "rows": limit}))
    out = []
    for w in data.get("workflows", [])[:limit]:
        nodes = []
        for n in w.get("nodes") or []:
            dn = n.get("displayName")
            if dn and dn not in nodes:
                nodes.append(dn)
        out.append({
            "name": w.get("name"),
            "url": f"https://n8n.io/workflows/{w.get('id')}",
            "views": w.get("totalViews"),
            "price": w.get("price") or 0,
            "created": (w.get("createdAt") or "")[:10],
            "nodes": nodes[:10],
            "author_verified": (w.get("user") or {}).get("verified"),
        })
    return out


def search_github(q, limit):
    url = "https://api.github.com/search/repositories?" + urllib.parse.urlencode(
        {"q": q, "sort": "stars", "order": "desc", "per_page": limit}
    )
    data = _get(url, _gh_headers())
    out = []
    for r in data.get("items", [])[:limit]:
        out.append({
            "name": r.get("full_name"),
            "description": _short(r.get("description")),
            "url": r.get("html_url"),
            "stars": r.get("stargazers_count"),
            "last_push": (r.get("pushed_at") or "")[:10],
            "created": (r.get("created_at") or "")[:10],
            "stars_per_month": _per_month(r.get("stargazers_count"), r.get("created_at")),
            "archived": r.get("archived"),
            "license": (r.get("license") or {}).get("spdx_id"),
            "topics": (r.get("topics") or [])[:8],
        })
    return out


def search_plugin(q, limit):
    if not GH_TOKEN:
        raise RuntimeError("needs `gh auth login` (GitHub code search requires a token)")
    url = "https://api.github.com/search/code?" + urllib.parse.urlencode(
        {"q": f"{q} filename:marketplace.json path:.claude-plugin", "per_page": limit}
    )
    data = _get(url, _gh_headers())
    out = []
    for it in data.get("items", [])[:limit]:
        repo = it.get("repository", {}).get("full_name")
        out.append({
            "name": repo,
            "url": f"https://github.com/{repo}",
            "install": f"/plugin marketplace add {repo}",
        })
    return out


PLUGIN_DIR = os.path.expanduser("~/.claude/plugins")
_OFFICIAL = None


def _norm_repo(url):
    m = GH_RE.search(url or "")
    return f"{m.group(1)}/{m.group(2).removesuffix('.git')}".lower() if m else None


def _load_official():
    """Claude Code's own local caches: the plugin directory (review state) and the
    official marketplace catalog (unique installs, token cost). Nothing leaves the Mac."""
    global _OFFICIAL
    if _OFFICIAL is not None:
        return _OFFICIAL
    entries = {}
    try:
        with open(os.path.join(PLUGIN_DIR, "plugin-directory-cache-v2.json")) as f:
            for l in json.load(f).get("listings", []):
                repo = (l.get("source", {}).get("repository") or {}).get("url")
                key = _norm_repo(repo) or (l.get("name") or "").lower()
                rv = (l.get("checks") or {}).get("review") or {}
                entries[key] = {
                    "name": l.get("name"), "description": l.get("summary") or "", "url": repo,
                    "review": f"{rv.get('state')}/{(rv.get('by') or {}).get('type')}" if rv.get("state") else "unreviewed",
                }
    except (OSError, ValueError):
        pass
    try:
        with open(os.path.join(PLUGIN_DIR, "plugin-catalog-cache.json")) as f:
            cat = json.load(f).get("catalog", {})
        model = (cat.get("models") or [None])[-1]
        for key, p in (cat.get("plugins") or {}).items():
            me = p.get("marketplace_entry") or {}
            src = me.get("source") if isinstance(me.get("source"), dict) else {}
            repo = src.get("url") or me.get("homepage")
            k = _norm_repo(repo)
            if k and src.get("path"):
                k = k + "#" + src["path"]  # monorepos hold several plugins
            e = entries.setdefault(k or key, {"name": me.get("name"), "url": repo, "review": "official-marketplace"})
            e.update({
                "name": me.get("name") or e.get("name"),
                "description": me.get("description") or e.get("description", ""),
                "category": me.get("category"),
                "unique_installs": p.get("unique_installs"),
                "tokens": (p.get("tokens") or {}).get(model),
                "tokens_model": model,
                "updated": (p.get("last_updated") or "")[:10],
                "install": f"/plugin install {key}",
            })
    except (OSError, ValueError):
        pass
    _OFFICIAL = list(entries.values())
    return _OFFICIAL


def search_official(q, limit):
    words = [w.lower() for w in re.findall(r"[A-Za-z0-9]+", q) if len(w) >= 2]
    scored = []
    for e in _load_official():
        hay = f"{e.get('name') or ''} {e.get('description') or ''} {e.get('category') or ''}".lower()
        score = sum(1 for w in words if re.search(r"(?<![a-z0-9])" + re.escape(w), hay))
        if score:
            scored.append((score, e.get("unique_installs") or 0, e))
    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    out = []
    for score, _, e in scored[:limit]:
        it = dict(e)
        it["description"] = _short(it.get("description"))
        it["word_matches"] = f"{score}/{len(words)}"
        out.append(it)
    return out


SOURCES = {
    "official": search_official,
    "mcp": search_mcp,
    "skill": search_skill,
    "workflow": search_workflow,
    "github": search_github,
    "plugin": search_plugin,
}

RUNS_DIR = os.path.expanduser("~/.cache/tool-finder/runs")


def brief_lines(results, linked, cap=12):
    """One short line per candidate: what the main model reads instead of the raw JSON."""
    lines = []
    for src, items in results.items():
        for i, it in enumerate(items[:cap]):
            sig = ""
            if it.get("stars") is not None:
                sig = f"★{it['stars']} ({it.get('stars_per_month')}/mo, since {(it.get('created') or '')[:7]})"
            elif it.get("installs") is not None: sig = f"inst {it['installs']}"
            elif src == "official":
                t = it.get("tokens") or {}
                sig = f"{it.get('review')}" + (f", inst {it['unique_installs']}" if it.get("unique_installs") else "") \
                      + (f", tok {t.get('always_on')}/{t.get('on_invoke')}" if t else "")
            elif src == "official":
                t = it.get("tokens") or {}
                sig = f"{it.get('review')}" + (f", inst {it['unique_installs']}" if it.get("unique_installs") else "") \
                      + (f", tok {t.get('always_on')}/{t.get('on_invoke')}" if t else "")
            elif it.get("views") is not None: sig = f"views {it['views']}"
            date = it.get("last_push") or it.get("updated") or it.get("created") or ""
            desc = (it.get("description") or it.get("title") or "")
            if src == "workflow":
                desc = "nodes: " + ", ".join(it.get("nodes", [])[:6])
            elif src == "skill":
                desc = "repo: " + (it.get("source_repo") or "")
            flag = " [archived]" if it.get("archived") else ""
            lines.append(f"{src[:3]}#{i} | {it.get('name')} | {sig} | {date[:7]}{flag} | {desc[:90]}")
        if len(items) > cap:
            lines.append(f"{src[:3]} … +{len(items) - cap} more in JSON")
    for g in linked:
        lines.append("linked | " + g["repo"] + " | " + ", ".join(f"{k}:{len(v)}" for k, v in g["seen_in"].items()))
    return "\n".join(lines)


GH_RE = re.compile(r"github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)")


def _repo_key(it):
    for field in ("url", "github", "source_repo", "name"):
        v = it.get(field) or ""
        m = GH_RE.search(v)
        if m:
            return f"{m.group(1)}/{m.group(2).removesuffix('.git')}".lower()
    if it.get("source_repo"):
        return it["source_repo"].lower()
    return None


def link_across_sources(results):
    """Group entries from different sources that point at the same GitHub repo.

    A repo that is at once an MCP server, a skill and a plugin marketplace is one
    project seen through several directories; showing that is what a single
    directory cannot do.
    """
    groups = {}
    for src, items in results.items():
        for it in items:
            k = _repo_key(it)
            if not k:
                continue
            g = groups.setdefault(k, {"repo": f"https://github.com/{k}", "seen_in": {}})
            g["seen_in"].setdefault(src, []).append(it.get("name"))
    return sorted((g for g in groups.values() if len(g["seen_in"]) > 1),
                  key=lambda g: -len(g["seen_in"]))


DEDUP_KEY = {"official": "name", "mcp": "name", "skill": "url", "workflow": "url", "github": "url", "plugin": "url"}


def main():
    global GH_TOKEN
    ap = argparse.ArgumentParser()
    ap.add_argument("queries", nargs="+", help="English keyword queries")
    ap.add_argument("--limit", type=int, default=8, help="results per query per source")
    ap.add_argument("--sources", default=",".join(SOURCES), help="comma-separated subset")
    ap.add_argument("--out", help="write full JSON here and print only a summary")
    ap.add_argument("--cap", type=int, default=12, help="max lines per source in --brief output")
    ap.add_argument("--brief", action="store_true",
                    help="save full JSON under ~/.cache/tool-finder/runs and print one line per candidate")
    args = ap.parse_args()

    GH_TOKEN = _gh_token()
    sources = [s.strip() for s in args.sources.split(",") if s.strip() in SOURCES]

    jobs = [(src, q) for src in sources for q in args.queries]
    results = {src: [] for src in sources}
    errors = []

    with ThreadPoolExecutor(max_workers=12) as ex:
        futs = {ex.submit(_limited(src, SOURCES[src]), q, args.limit): (src, q) for src, q in jobs}
        for fut, (src, q) in futs.items():
            try:
                for item in fut.result():
                    item["matched_query"] = q
                    results[src].append(item)
            except Exception as e:  # keep going; report which source failed
                errors.append({"source": src, "query": q, "error": _short(str(e), 200)})

    for src, items in results.items():
        seen, uniq = set(), []
        for it in items:
            k = it.get(DEDUP_KEY[src])
            if k in seen:
                continue
            seen.add(k)
            uniq.append(it)
        results[src] = uniq

    report = {"queries": args.queries, "results": results,
              "linked": link_across_sources(results), "errors": errors}
    text = json.dumps(report, ensure_ascii=False, indent=1)
    out = args.out
    if args.brief and not out:
        os.makedirs(RUNS_DIR, mode=0o700, exist_ok=True)
        out = os.path.join(RUNS_DIR, dt.datetime.now().strftime("%Y%m%d-%H%M%S") + ".json")
    if out:
        with open(out, "w") as f:
            f.write(text + "\n")
        os.chmod(out, 0o600)
        counts = {k: len(v) for k, v in results.items()}
        print(json.dumps({"saved": out, "counts": counts,
                          "linked": len(report["linked"]), "errors": errors}, ensure_ascii=False))
        if args.brief:
            print(brief_lines(results, report["linked"], args.cap))
    else:
        print(text)


if __name__ == "__main__":
    main()
