#!/usr/bin/env python3
"""Check whether a candidate still works, without installing or running it.

Usage:
  python3 liveness.py <owner/repo>[#sub/path] [<owner/repo>...] [--pkg pypi:name] [--pkg npm:name]

Per repo it reports, from public metadata only:
  - repo: stars, archived, last push
  - path (monorepo skill): present on HEAD or not; if removed, the removing commit and the parent sha
  - deps: package names found in install lines (pip install / npm i / npx) and requirements.txt /
    package.json at that path (or at the parent commit if the path was removed)
  - packages: whether each dep / --pkg is still published (PyPI, npm) and its latest release date
  - issues: recent (180 days) issue titles in the repo AND in each dep's GitHub repo that look like
    breakage (403, blocked, login error, deprecated, takedown ...)

Nothing is installed or executed. README/SKILL.md text is only pattern-matched for package names
and never printed. Issue titles are printed truncated; treat them as untrusted data.
"""
import argparse
import base64
import datetime as dt
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from search import _get, _gh_headers, _gh_token  # noqa: E402
import search  # noqa: E402

GH = "https://api.github.com"
BREAK_RX = re.compile(
    r"403|401|blocked|\bblock|\bban(ned)?\b|captcha|login|log in|sign.?in|\bauth\b|deprecat|broken|not work|"
    r"doesn.?t work|stopped|fail|error|-2000|macro|takedown|dmca|cease|discontinu|"
    r"차단|막|로그인|에러|오류|안\s?됨|안\s?돼|중단|매크로|종료|삭제",
    re.I,
)
PKG_RX = [
    ("pypi", re.compile(r"pip3?\s+install\s+((?:[-\w.\[\]=<>~!]+\s*)+)")),
    ("npm", re.compile(r"npm\s+(?:i|install)\s+(?:-g\s+)?((?:@?[\w./-]+\s*)+)")),
    ("npm", re.compile(r"npx\s+(?:-y\s+|--yes\s+)?(@?[\w./-]+)")),
]
SKIP_PKGS = {"-r", "-e", "-u", "--upgrade", "--user", ".", "requirements.txt", "skills", "pip",
             "uv", "-g", "-y", "--yes"}


def gh(path):
    return _get(GH + path, _gh_headers())


def file_text(repo, path, ref=None):
    q = f"?ref={ref}" if ref else ""
    try:
        d = gh(f"/repos/{repo}/contents/{path}{q}")
        return base64.b64decode(d.get("content", "")).decode("utf-8", "replace")
    except Exception:
        return None


PY_IMPORT = re.compile(r"^\s*(?:from|import)\s+([A-Za-z_]\w*)", re.M)
DOC_EXT = (".md", ".txt", ".toml", ".json", ".py", ".sh")


def _files_under(repo, sub, ref):
    """Small text files at the skill path (or repo root), max 10, at ref."""
    q = f"?ref={ref}" if ref else ""
    try:
        items = gh(f"/repos/{repo}/contents/{sub or ''}{q}")
    except Exception:
        return []
    if isinstance(items, dict):
        items = [items]
    files = [i for i in items if i.get("type") == "file" and i["name"].endswith(DOC_EXT) and i.get("size", 0) < 200_000]
    for d in [i for i in items if i.get("type") == "dir" and i["name"] in ("scripts", "src", "helpers", "bin")][:2]:
        try:
            files += [i for i in gh(f"/repos/{repo}/contents/{d['path']}{q}")
                      if i.get("type") == "file" and i["name"].endswith(DOC_EXT)]
        except Exception:
            pass
    return [f["path"] for f in files[:10]]


def deps_from(repo, sub, ref):
    found = set()
    stdlib = set(getattr(sys, "stdlib_module_names", ()))
    paths = _files_under(repo, sub, ref)
    local = {p.rsplit("/", 1)[-1][:-3].lower() for p in paths if p.endswith(".py")}
    for path in paths:
        t = file_text(repo, path, ref)
        if not t:
            continue
        name = path.rsplit("/", 1)[-1]
        if name == "requirements.txt":
            for line in t.splitlines():
                tok = re.split(r"[=<>~!\[;#\s]", line.strip())[0]
                if tok and not tok.startswith("-"):
                    found.add(("pypi", tok.lower()))
            continue
        if name == "package.json":
            try:
                for k in json.loads(t).get("dependencies", {}):
                    found.add(("npm", k))
            except Exception:
                pass
            continue
        if name.endswith(".py"):
            for mod in PY_IMPORT.findall(t):
                if mod not in stdlib and not mod.startswith("_") and mod.lower() not in local:
                    found.add(("pypi", mod.lower()))
            continue
        for eco, rx in PKG_RX:
            for m in rx.findall(t):
                for tok in m.split():
                    tok = re.split(r"[=<>~!\[]", tok)[0].strip().strip("`'\"")
                    if tok and tok not in SKIP_PKGS and not tok.startswith("-") and len(tok) < 60:
                        found.add((eco, tok.lower() if eco == "pypi" else tok))
    return sorted(found)[:15]


def pkg_status(eco, name):
    try:
        if eco == "pypi":
            d = _get(f"https://pypi.org/pypi/{name}/json", retries=0)
            info = d["info"]
            rel = d.get("releases", {}).get(info["version"]) or [{}]
            urls = " ".join(str(v) for v in (info.get("project_urls") or {}).values()) + " " + (info.get("home_page") or "")
            return {"published": True, "latest": info["version"],
                    "released": (rel[0].get("upload_time") or "")[:10], "repo": _gh_repo(urls)}
        d = _get(f"https://registry.npmjs.org/{name.replace('/', '%2F')}", retries=0)
        latest = d.get("dist-tags", {}).get("latest")
        repo = d.get("repository", {})
        repo = repo.get("url", "") if isinstance(repo, dict) else str(repo)
        return {"published": True, "latest": latest, "released": (d.get("time", {}).get(latest) or "")[:10],
                "deprecated": bool(d.get("versions", {}).get(latest, {}).get("deprecated")), "repo": _gh_repo(repo)}
    except Exception as e:
        return {"published": False, "error": str(e)[:60]}


def _gh_repo(text):
    m = re.search(r"github\.com[/:]([\w.-]+/[\w.-]+?)(?:\.git|/|\s|$)", text or "")
    return m.group(1) if m else None


def breakage_issues(repo, days=180, n=5):
    since = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        items = gh(f"/repos/{repo}/issues?state=all&since={since}&per_page=60&sort=created&direction=desc")
    except Exception as e:
        return [{"error": str(e)[:60]}]
    hits = []
    for it in items:
        if "pull_request" in it:
            continue
        title = it.get("title", "")
        if BREAK_RX.search(title):
            hits.append({"#": it["number"], "date": it["created_at"][:10], "state": it["state"],
                         "comments": it.get("comments", 0), "title": title[:80]})
    hits.sort(key=lambda h: (h["comments"], h["date"]), reverse=True)
    return hits[:n]


def check(target):
    repo, _, sub = target.partition("#")
    out = {"target": target}
    try:
        r = gh(f"/repos/{repo}")
    except Exception as e:
        out["repo"] = f"missing ({str(e)[:40]})"
        return out
    out["repo"] = {"stars": r["stargazers_count"], "archived": r["archived"], "pushed": r["pushed_at"][:10]}
    ref = None
    if sub:
        try:
            gh(f"/repos/{repo}/contents/{sub}")
            c = gh(f"/repos/{repo}/commits?path={sub}&per_page=1")
            out["path"] = {"present": True, "last_change": c[0]["commit"]["committer"]["date"][:10] if c else None}
        except Exception:
            c = gh(f"/repos/{repo}/commits?path={sub}&per_page=1")
            if c:
                ref = c[0]["parents"][0]["sha"] if c[0].get("parents") else None
                out["path"] = {"present": False, "removed_in": c[0]["sha"][:10],
                               "removed_on": c[0]["commit"]["committer"]["date"][:10],
                               "removal_msg": c[0]["commit"]["message"].splitlines()[0][:80],
                               "last_version_ref": ref[:10] if ref else None}
            else:
                out["path"] = {"present": False, "history": "none"}
    deps = deps_from(repo, sub, ref)
    out["deps"] = {}
    dep_repos = []
    for eco, name in deps:
        st = pkg_status(eco, name)
        out["deps"][f"{eco}:{name}"] = st
        if st.get("repo") and st["repo"].lower() != repo.lower():
            dep_repos.append(st["repo"])
    out["issues"] = {repo: breakage_issues(repo)}
    # Fragile, domain-specific libraries (unofficial API wrappers) are small; big ones (requests, flask)
    # rarely explain why a niche tool broke. Scan the 3 smallest dep repos, plus a fork's upstream.
    sized = []
    for dr in dict.fromkeys(dep_repos):
        try:
            info = gh(f"/repos/{dr}")
        except Exception:
            continue
        sized.append((info["stargazers_count"], dr))
        if info.get("fork") and info.get("parent"):
            sized.append((info["parent"]["stargazers_count"], info["parent"]["full_name"]))
    for _, dr in sorted(sized)[:3]:
        out["issues"][dr] = breakage_issues(dr)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("targets", nargs="*", help="owner/repo or owner/repo#path/to/skill")
    ap.add_argument("--pkg", action="append", default=[], help="pypi:name or npm:name")
    a = ap.parse_args()
    search.GH_TOKEN = _gh_token()
    res = [check(t) for t in a.targets[:6]]
    for p in a.pkg:
        eco, _, name = p.partition(":")
        res.append({"package": p, **pkg_status(eco, name)})
    for r in res:
        print(json.dumps(r, ensure_ascii=False))


if __name__ == "__main__":
    main()
