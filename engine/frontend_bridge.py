import json
import os
import subprocess
from pathlib import Path

from flask import Response, render_template, request, url_for

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
FRONTEND_CLIENT_ROOT = FRONTEND_DIR / "dist" / "client"
FRONTEND_ASSETS_ROOT = FRONTEND_CLIENT_ROOT / "assets"
FRONTEND_SERVER_ENTRY = FRONTEND_DIR / "dist" / "server" / "index.js"

_frontend_bundle_cache = None
_frontend_ssr_script = """
const requestUrl = process.argv[1];
const { default: serverEntry } = await import('./dist/server/index.js');
const response = await serverEntry.fetch(new Request(requestUrl));
const body = await response.text();
const payload = {
  status: response.status,
  headers: Object.fromEntries(response.headers.entries()),
  body,
};
process.stdout.write(JSON.stringify(payload));
"""


def _get_frontend_bundle():
    global _frontend_bundle_cache
    if _frontend_bundle_cache:
        return _frontend_bundle_cache

    if not FRONTEND_ASSETS_ROOT.is_dir():
        return None

    css_name = None
    entry_name = None
    for item in sorted(os.listdir(FRONTEND_ASSETS_ROOT)):
        if item.startswith("styles-") and item.endswith(".css"):
            css_name = item
    for item in sorted(os.listdir(FRONTEND_ASSETS_ROOT)):
        if item.startswith("index-") and item.endswith(".js"):
            file_path = FRONTEND_ASSETS_ROOT / item
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if "hydrateRoot" in content or "createRouter" in content:
                entry_name = item
                break

    if not css_name or not entry_name:
        return None

    _frontend_bundle_cache = {
        "styles_href": url_for("frontend_client_route", filename=f"assets/{css_name}"),
        "entry_href": url_for("frontend_client_route", filename=f"assets/{entry_name}"),
    }
    return _frontend_bundle_cache


def _inject_frontend_path(html, frontend_path):
    target_path = frontend_path or request.path
    if not target_path or target_path == request.path:
        return html
    script = (
        "<script>(function(){var p="
        + json.dumps(target_path)
        + ";var u=p+window.location.search+window.location.hash;"
        + "if(window.location.pathname!==p){window.history.replaceState({},'',u);}})();</script>"
    )
    if "<head>" in html:
        return html.replace("<head>", f"<head>{script}", 1)
    return script + html


def render_frontend(frontend_path=None):
    rendered = render_frontend_ssr(frontend_path=frontend_path)
    if rendered is not None:
        return rendered
    bundle = _get_frontend_bundle()
    if not bundle:
        return render_template(
            "loveable_shell.html",
            styles_href=None,
            entry_href=None,
            frontend_path=frontend_path or request.path,
        )
    return render_template(
        "loveable_shell.html",
        styles_href=bundle["styles_href"],
        entry_href=bundle["entry_href"],
        frontend_path=frontend_path or request.path,
    )


def render_frontend_ssr(frontend_path=None):
    if not FRONTEND_SERVER_ENTRY.is_file():
        return None

    target_path = frontend_path or request.path
    request_url = f"http://localhost{target_path}"
    if request.query_string:
        request_url = f"{request_url}?{request.query_string.decode('utf-8', errors='ignore')}"

    try:
        completed = subprocess.run(
            ["node", "--input-type=module", "-e", _frontend_ssr_script, request_url],
            cwd=FRONTEND_DIR,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None

    if completed.returncode != 0 or not completed.stdout:
        return None

    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return None

    body = _inject_frontend_path(payload.get("body") or "", frontend_path)
    headers = payload.get("headers") or {}
    content_type = headers.get("content-type", "text/html; charset=utf-8")
    return Response(body, status=payload.get("status", 200), content_type=content_type)


def should_render_frontend_html():
    if (request.args.get("format") or "").strip().lower() == "json":
        return False
    best = request.accept_mimetypes.best_match(["text/html", "application/json"])
    if best is None:
        return True
    if best == "application/json":
        return False
    return request.accept_mimetypes[best] >= request.accept_mimetypes["application/json"]
