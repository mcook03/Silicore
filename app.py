import os
from collections import defaultdict

from flask import (
    Flask,
    flash,
    redirect,
    render_template_string,
    request,
    send_from_directory,
    url_for,
)

from engine.config_loader import save_config, parse_config_form
from engine.dashboard_storage import get_recent_runs
from engine.services.analysis_service import (
    analyze_project_files,
    analyze_single_board,
    get_dashboard_config,
)

app = Flask(__name__)
app.secret_key = "silicore-dev-secret"

UPLOAD_FOLDER = "dashboard_uploads"
RUNS_FOLDER = "dashboard_runs"
CONFIG_PATH = "custom_config.json"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RUNS_FOLDER, exist_ok=True)


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _severity_rank(severity):
    order = {
        "critical": 0,
        "high": 1,
        "medium": 2,
        "low": 3,
    }
    return order.get(str(severity).lower(), 4)


def _format_category_name(category):
    if not category:
        return "Uncategorized"
    return str(category).replace("_", " ").title()


def _prepare_grouped_risks(risks):
    grouped = defaultdict(list)

    for risk in risks or []:
        category = risk.get("category", "uncategorized")
        grouped[category].append(risk)

    grouped_sections = []
    for category, items in grouped.items():
        sorted_items = sorted(
            items,
            key=lambda item: (
                _severity_rank(item.get("severity")),
                item.get("message", ""),
            ),
        )

        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for item in sorted_items:
            sev = str(item.get("severity", "")).lower()
            if sev in severity_counts:
                severity_counts[sev] += 1

        grouped_sections.append(
            {
                "key": category,
                "title": _format_category_name(category),
                "risks": sorted_items,
                "count": len(sorted_items),
                "severity_counts": severity_counts,
            }
        )

    grouped_sections.sort(
        key=lambda section: (
            min(
                [_severity_rank(risk.get("severity")) for risk in section["risks"]] or [99]
            ),
            section["title"],
        )
    )

    return grouped_sections


def _prepare_top_issues(risks, limit=3):
    sorted_risks = sorted(
        risks or [],
        key=lambda item: (
            _severity_rank(item.get("severity")),
            item.get("category", ""),
            item.get("message", ""),
        ),
    )
    return sorted_risks[:limit]


def _build_health_summary(score, risks):
    score_value = _safe_float(score, 0.0)
    risk_count = len(risks or [])
    critical_count = sum(
        1 for risk in (risks or []) if str(risk.get("severity", "")).lower() == "critical"
    )
    high_count = sum(
        1 for risk in (risks or []) if str(risk.get("severity", "")).lower() == "high"
    )

    if score_value >= 8.5 and critical_count == 0:
        return {
            "title": "Strong board health",
            "summary": "This board looks solid overall. Remaining issues appear targeted rather than systemic.",
        }

    if critical_count > 0:
        return {
            "title": "Critical review needed",
            "summary": "At least one critical issue is present. This board should be reviewed before release decisions.",
        }

    if high_count >= 3 or score_value < 5.0:
        return {
            "title": "Needs engineering attention",
            "summary": "This board has multiple high-impact issues that could affect implementation quality or reliability.",
        }

    if risk_count == 0:
        return {
            "title": "No issues detected",
            "summary": "No findings were produced under the current ruleset and configuration.",
        }

    return {
        "title": "Moderate review recommended",
        "summary": "The board is workable, but there are still a few meaningful issues worth cleaning up.",
    }


def _build_project_health_summary(project_result):
    project_summary = project_result.get("project_summary", {}) or {}
    boards = project_result.get("boards", []) or []
    average_score = _safe_float(project_summary.get("average_score", 0), 0.0)
    best_score = _safe_float(project_summary.get("best_score", 0), 0.0)
    worst_score = _safe_float(project_summary.get("worst_score", 0), 0.0)

    if not boards:
        return {
            "title": "No boards analyzed",
            "summary": "Upload a project set to compare boards and see project-wide engineering health.",
        }

    if average_score >= 8.0 and worst_score >= 7.0:
        return {
            "title": "Strong project baseline",
            "summary": "The uploaded boards are consistently healthy and do not show major spread in quality.",
        }

    if worst_score < 5.0 and best_score >= 8.0:
        return {
            "title": "Large project quality spread",
            "summary": "Some boards are in strong shape while at least one design needs much deeper engineering attention.",
        }

    if average_score < 6.0:
        return {
            "title": "Project review recommended",
            "summary": "The overall project trend shows enough risk that broader cleanup is worth doing before release confidence increases.",
        }

    return {
        "title": "Mixed but manageable",
        "summary": "The project has a workable baseline, but board quality is not yet consistently strong across the set.",
    }


def _enrich_single_result(result):
    risks = result.get("risks", []) or []
    result["grouped_risks"] = _prepare_grouped_risks(risks)
    result["top_issues"] = _prepare_top_issues(risks)
    result["health_summary"] = _build_health_summary(result.get("score", 0), risks)
    return result


def _enrich_project_result(project_result):
    boards = project_result.get("boards", []) or []

    for board in boards:
        board_risks = board.get("risks", []) or []
        board["top_issues"] = _prepare_top_issues(board_risks, limit=2)
        board["health_summary"] = _build_health_summary(board.get("score", 0), board_risks)

    project_result["project_health_summary"] = _build_project_health_summary(project_result)
    return project_result


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Silicore Dashboard</title>
    <style>
        :root {
            --bg-0: #050816;
            --bg-1: #09101d;
            --bg-2: #0d1526;
            --panel: rgba(13, 21, 38, 0.82);
            --panel-strong: rgba(18, 29, 51, 0.94);
            --panel-soft: rgba(255, 255, 255, 0.04);
            --border: rgba(129, 171, 255, 0.14);
            --border-strong: rgba(129, 171, 255, 0.24);
            --text: #eef4ff;
            --muted: #98a9c6;
            --muted-2: #7b8cac;
            --blue: #6eb5ff;
            --blue-2: #4f8dff;
            --cyan: #63f0ff;
            --violet: #9b7cff;
            --green: #62e6a7;
            --yellow: #ffd778;
            --red: #ff8f9e;
            --critical: #ff6f85;
            --shadow-xl: 0 30px 80px rgba(0, 0, 0, 0.42);
            --shadow-lg: 0 18px 40px rgba(0, 0, 0, 0.30);
            --shadow-md: 0 12px 26px rgba(0, 0, 0, 0.18);
            --radius-xl: 26px;
            --radius-lg: 20px;
            --radius-md: 16px;
            --radius-sm: 12px;
        }

        * {
            box-sizing: border-box;
        }

        html {
            scroll-behavior: smooth;
        }

        body {
            margin: 0;
            font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            color: var(--text);
            background:
                radial-gradient(circle at top left, rgba(79, 141, 255, 0.15), transparent 28%),
                radial-gradient(circle at top right, rgba(155, 124, 255, 0.12), transparent 24%),
                radial-gradient(circle at 50% 120%, rgba(99, 240, 255, 0.10), transparent 26%),
                linear-gradient(180deg, var(--bg-0) 0%, var(--bg-1) 45%, var(--bg-2) 100%);
            min-height: 100vh;
            overflow-x: hidden;
        }

        body::before {
            content: "";
            position: fixed;
            inset: 0;
            pointer-events: none;
            background:
                linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px);
            background-size: 36px 36px;
            mask-image: linear-gradient(180deg, rgba(0,0,0,0.4), rgba(0,0,0,0.08));
            opacity: 0.28;
        }

        a {
            color: var(--blue);
            text-decoration: none;
        }

        .app-shell {
            width: min(1460px, calc(100% - 34px));
            margin: 0 auto;
            padding: 26px 0 40px;
        }

        .topbar {
            position: sticky;
            top: 14px;
            z-index: 40;
            margin-bottom: 20px;
            backdrop-filter: blur(18px);
            -webkit-backdrop-filter: blur(18px);
            background: rgba(8, 13, 25, 0.6);
            border: 1px solid rgba(137, 176, 255, 0.10);
            border-radius: 18px;
            box-shadow: var(--shadow-md);
            padding: 12px 16px;
        }

        .topbar-inner {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 18px;
        }

        .brand-wrap {
            display: flex;
            align-items: center;
            gap: 14px;
        }

        .brand-mark {
            width: 46px;
            height: 46px;
            border-radius: 14px;
            background:
                radial-gradient(circle at 30% 30%, rgba(255,255,255,0.35), transparent 30%),
                linear-gradient(135deg, rgba(110,181,255,0.95), rgba(79,141,255,0.65) 55%, rgba(155,124,255,0.8));
            box-shadow:
                inset 0 1px 0 rgba(255,255,255,0.22),
                0 10px 30px rgba(79,141,255,0.30);
            position: relative;
        }

        .brand-mark::after {
            content: "";
            position: absolute;
            inset: 10px;
            border-radius: 10px;
            border: 1px solid rgba(255,255,255,0.28);
        }

        .brand-copy {
            display: grid;
            gap: 4px;
        }

        .brand-title {
            font-size: 18px;
            font-weight: 800;
            letter-spacing: 0.02em;
        }

        .brand-sub {
            color: var(--muted);
            font-size: 12px;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }

        .topbar-badges {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }

        .top-badge {
            padding: 10px 12px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 700;
            color: #dbebff;
            border: 1px solid rgba(125, 167, 255, 0.14);
            background: rgba(255,255,255,0.04);
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.04);
        }

        .hero {
            position: relative;
            overflow: hidden;
            background:
                linear-gradient(145deg, rgba(14,22,39,0.88), rgba(14,22,39,0.65)),
                radial-gradient(circle at 12% 20%, rgba(99,240,255,0.10), transparent 20%),
                radial-gradient(circle at 88% 18%, rgba(155,124,255,0.14), transparent 24%),
                linear-gradient(135deg, rgba(79,141,255,0.22), rgba(79,141,255,0.00) 48%);
            border: 1px solid var(--border);
            border-radius: 30px;
            box-shadow: var(--shadow-xl);
            padding: 34px;
            margin-bottom: 22px;
        }

        .hero::before {
            content: "";
            position: absolute;
            inset: 0;
            background:
                linear-gradient(90deg, transparent, rgba(255,255,255,0.06), transparent);
            transform: translateX(-100%);
            animation: heroSweep 9s linear infinite;
            pointer-events: none;
        }

        @keyframes heroSweep {
            0% { transform: translateX(-100%); }
            40% { transform: translateX(100%); }
            100% { transform: translateX(100%); }
        }

        .hero-eyebrow {
            display: inline-flex;
            align-items: center;
            gap: 10px;
            padding: 8px 12px;
            border-radius: 999px;
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(115, 167, 255, 0.16);
            color: #bdd6ff;
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 16px;
        }

        .hero-grid {
            display: grid;
            grid-template-columns: 1.2fr 0.8fr;
            gap: 26px;
            align-items: center;
        }

        .hero h1 {
            margin: 0 0 12px;
            font-size: 56px;
            line-height: 0.98;
            letter-spacing: -0.04em;
        }

        .hero p {
            margin: 0;
            color: var(--muted);
            font-size: 16px;
            line-height: 1.75;
            max-width: 860px;
        }

        .hero-chip-row {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            margin-top: 22px;
        }

        .hero-chip {
            padding: 11px 14px;
            border-radius: 14px;
            color: #dfeeff;
            font-size: 13px;
            font-weight: 700;
            background: rgba(255,255,255,0.035);
            border: 1px solid rgba(130, 171, 255, 0.14);
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.04);
        }

        .hero-status-card {
            position: relative;
            background: linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02));
            border: 1px solid rgba(130,171,255,0.14);
            border-radius: 24px;
            padding: 22px;
            box-shadow: var(--shadow-lg);
            overflow: hidden;
        }

        .hero-status-card::before {
            content: "";
            position: absolute;
            inset: auto -20% -42% auto;
            width: 220px;
            height: 220px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(99,240,255,0.14), transparent 60%);
            pointer-events: none;
        }

        .status-kicker {
            color: #b7d1ff;
            font-size: 12px;
            font-weight: 800;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 12px;
        }

        .status-number {
            font-size: 44px;
            font-weight: 900;
            letter-spacing: -0.04em;
            margin-bottom: 8px;
        }

        .status-copy {
            color: var(--muted);
            line-height: 1.65;
            font-size: 14px;
        }

        .flash-stack {
            display: grid;
            gap: 12px;
            margin-bottom: 18px;
        }

        .flash {
            background: linear-gradient(180deg, rgba(24, 39, 70, 0.9), rgba(17, 28, 48, 0.9));
            border: 1px solid rgba(110,181,255,0.18);
            color: #e5f1ff;
            padding: 14px 16px;
            border-radius: 16px;
            box-shadow: var(--shadow-md);
        }

        .main-grid {
            display: grid;
            grid-template-columns: 380px minmax(0, 1fr);
            gap: 22px;
            align-items: start;
        }

        .sidebar,
        .content {
            display: grid;
            gap: 18px;
        }

        .card {
            position: relative;
            overflow: hidden;
            background:
                linear-gradient(180deg, rgba(14, 22, 39, 0.94), rgba(10, 17, 31, 0.92));
            border: 1px solid var(--border);
            border-radius: var(--radius-xl);
            box-shadow: var(--shadow-lg);
            backdrop-filter: blur(18px);
            -webkit-backdrop-filter: blur(18px);
        }

        .card::before {
            content: "";
            position: absolute;
            inset: 0 0 auto 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.16), transparent);
            opacity: 0.7;
            pointer-events: none;
        }

        .card-header {
            padding: 22px 22px 0;
        }

        .card-body {
            padding: 18px 22px 22px;
        }

        .section-title {
            margin: 0;
            font-size: 20px;
            line-height: 1.2;
            letter-spacing: -0.02em;
        }

        .section-copy {
            margin: 9px 0 0;
            color: var(--muted);
            line-height: 1.6;
            font-size: 14px;
        }

        .divider {
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.10), transparent);
            margin: 6px 0 4px;
        }

        form {
            display: grid;
            gap: 14px;
        }

        label {
            display: grid;
            gap: 8px;
            font-size: 13px;
            color: #c5d8f5;
            font-weight: 700;
        }

        input[type="file"],
        input[type="text"],
        input[type="number"] {
            width: 100%;
            border-radius: 14px;
            border: 1px solid rgba(120, 155, 225, 0.16);
            padding: 13px 14px;
            color: var(--text);
            background:
                linear-gradient(180deg, rgba(255,255,255,0.04), rgba(255,255,255,0.02));
            box-shadow:
                inset 0 1px 0 rgba(255,255,255,0.04),
                0 0 0 0 rgba(110,181,255,0.00);
            outline: none;
            transition: border-color 0.18s ease, box-shadow 0.18s ease, transform 0.18s ease;
        }

        input[type="file"]:hover,
        input[type="text"]:hover,
        input[type="number"]:hover {
            border-color: rgba(130, 171, 255, 0.22);
        }

        input[type="file"]:focus,
        input[type="text"]:focus,
        input[type="number"]:focus {
            border-color: rgba(110,181,255,0.48);
            box-shadow:
                inset 0 1px 0 rgba(255,255,255,0.04),
                0 0 0 4px rgba(110,181,255,0.10),
                0 0 26px rgba(110,181,255,0.14);
            transform: translateY(-1px);
        }

        input::placeholder {
            color: #7184a3;
        }

        .stack {
            display: grid;
            gap: 16px;
        }

        .inline-grid-2 {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
        }

        .minor-title {
            margin: 0;
            font-size: 16px;
            font-weight: 800;
            letter-spacing: -0.02em;
        }

        .mini-note {
            color: var(--muted);
            font-size: 12px;
            line-height: 1.6;
        }

        .btn {
            appearance: none;
            position: relative;
            overflow: hidden;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            width: 100%;
            border: 0;
            cursor: pointer;
            border-radius: 15px;
            padding: 13px 16px;
            font-size: 14px;
            font-weight: 800;
            letter-spacing: 0.01em;
            transition:
                transform 0.16s ease,
                box-shadow 0.16s ease,
                filter 0.16s ease,
                border-color 0.16s ease;
            transform: translateY(0);
            user-select: none;
        }

        .btn::before {
            content: "";
            position: absolute;
            inset: 0;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.14), transparent);
            transform: translateX(-115%);
            transition: transform 0.6s ease;
        }

        .btn:hover::before {
            transform: translateX(115%);
        }

        .btn:active {
            transform: translateY(1px) scale(0.992);
        }

        .btn-primary {
            color: #06111f;
            background:
                linear-gradient(135deg, rgba(110,181,255,1), rgba(79,141,255,1) 55%, rgba(99,240,255,0.95));
            box-shadow:
                0 0 0 1px rgba(255,255,255,0.08) inset,
                0 14px 30px rgba(79,141,255,0.24),
                0 0 0 0 rgba(99,240,255,0.00);
        }

        .btn-primary:hover {
            box-shadow:
                0 0 0 1px rgba(255,255,255,0.12) inset,
                0 18px 36px rgba(79,141,255,0.28),
                0 0 28px rgba(99,240,255,0.18);
            filter: brightness(1.03);
            transform: translateY(-1px);
        }

        .btn-primary:active {
            box-shadow:
                0 0 0 1px rgba(255,255,255,0.12) inset,
                0 10px 22px rgba(79,141,255,0.22),
                0 0 36px rgba(99,240,255,0.30);
        }

        .btn-secondary {
            color: #e7f1ff;
            border: 1px solid rgba(132, 174, 255, 0.16);
            background:
                linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.03));
            box-shadow:
                inset 0 1px 0 rgba(255,255,255,0.06),
                0 12px 24px rgba(0,0,0,0.18);
        }

        .btn-secondary:hover {
            transform: translateY(-1px);
            box-shadow:
                inset 0 1px 0 rgba(255,255,255,0.08),
                0 16px 28px rgba(0,0,0,0.20),
                0 0 20px rgba(110,181,255,0.12);
            border-color: rgba(132,174,255,0.28);
        }

        .runs-list {
            display: grid;
            gap: 10px;
        }

        .run-item {
            padding: 14px;
            border-radius: 16px;
            background: linear-gradient(180deg, rgba(255,255,255,0.04), rgba(255,255,255,0.02));
            border: 1px solid rgba(127, 163, 229, 0.12);
            transition: transform 0.16s ease, border-color 0.16s ease, box-shadow 0.16s ease;
        }

        .run-item:hover {
            transform: translateY(-2px);
            border-color: rgba(127,163,229,0.22);
            box-shadow: 0 14px 26px rgba(0,0,0,0.18);
        }

        .run-title {
            margin: 0 0 6px;
            font-size: 14px;
            font-weight: 800;
        }

        .run-meta {
            color: var(--muted);
            font-size: 12px;
            line-height: 1.55;
        }

        .result-shell {
            display: grid;
            gap: 20px;
        }

        .metric-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 14px;
        }

        .metric-card {
            position: relative;
            overflow: hidden;
            background:
                linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.03));
            border: 1px solid rgba(124, 162, 229, 0.14);
            border-radius: 20px;
            padding: 18px;
            box-shadow: var(--shadow-md);
        }

        .metric-card::after {
            content: "";
            position: absolute;
            inset: auto auto -30px -30px;
            width: 120px;
            height: 120px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(110,181,255,0.10), transparent 60%);
            pointer-events: none;
        }

        .metric-label {
            color: #9eb4d2;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            margin-bottom: 10px;
            font-weight: 800;
        }

        .metric-value {
            font-size: 32px;
            font-weight: 900;
            line-height: 1.02;
            letter-spacing: -0.04em;
        }

        .metric-sub {
            margin-top: 8px;
            color: var(--muted);
            font-size: 13px;
            line-height: 1.5;
            position: relative;
            z-index: 1;
        }

        .score-band-excellent { color: #83efb7; }
        .score-band-good { color: #9fd2ff; }
        .score-band-watch { color: #ffd37a; }
        .score-band-risk { color: #ff9aa6; }

        .summary-strip {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 14px;
        }

        .summary-panel {
            position: relative;
            overflow: hidden;
            background:
                linear-gradient(180deg, rgba(255,255,255,0.05), rgba(255,255,255,0.025));
            border: 1px solid rgba(128, 168, 240, 0.14);
            border-radius: 20px;
            padding: 18px 18px 18px 18px;
            box-shadow: var(--shadow-md);
        }

        .summary-panel::before {
            content: "";
            position: absolute;
            top: 0;
            left: 18px;
            right: 18px;
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.16), transparent);
        }

        .summary-panel h3 {
            margin: 0 0 8px;
            font-size: 17px;
            letter-spacing: -0.02em;
        }

        .summary-panel p {
            margin: 0;
            color: var(--muted);
            line-height: 1.7;
            font-size: 14px;
        }

        .section-block-header {
            display: flex;
            align-items: end;
            justify-content: space-between;
            gap: 14px;
            margin-bottom: 10px;
        }

        .section-block-header .copy {
            color: var(--muted);
            font-size: 14px;
            line-height: 1.6;
        }

        .issues-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 14px;
        }

        .issue-card {
            position: relative;
            overflow: hidden;
            background:
                linear-gradient(180deg, rgba(255,255,255,0.05), rgba(255,255,255,0.03));
            border: 1px solid rgba(130,171,255,0.12);
            border-radius: 20px;
            padding: 18px;
            box-shadow: var(--shadow-md);
            min-height: 188px;
            transition: transform 0.16s ease, border-color 0.16s ease, box-shadow 0.16s ease;
        }

        .issue-card:hover {
            transform: translateY(-3px);
            border-color: rgba(130,171,255,0.22);
            box-shadow:
                0 18px 34px rgba(0,0,0,0.20),
                0 0 24px rgba(110,181,255,0.08);
        }

        .issue-card h4 {
            margin: 0 0 10px;
            font-size: 15px;
            line-height: 1.5;
        }

        .issue-meta {
            color: var(--muted);
            font-size: 12px;
            line-height: 1.5;
        }

        .chip {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-width: 78px;
            padding: 7px 11px;
            border-radius: 999px;
            font-size: 11px;
            font-weight: 900;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            margin-bottom: 12px;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.08);
        }

        .chip-critical {
            background: rgba(255,111,133,0.14);
            color: #ffbcc8;
            border: 1px solid rgba(255,111,133,0.18);
        }

        .chip-high {
            background: rgba(255,143,158,0.14);
            color: #ffd0d7;
            border: 1px solid rgba(255,143,158,0.18);
        }

        .chip-medium {
            background: rgba(255,215,120,0.14);
            color: #ffe4a7;
            border: 1px solid rgba(255,215,120,0.18);
        }

        .chip-low {
            background: rgba(98,230,167,0.12);
            color: #c9ffe5;
            border: 1px solid rgba(98,230,167,0.18);
        }

        .group-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 12px;
        }

        .group-card {
            background:
                linear-gradient(180deg, rgba(255,255,255,0.045), rgba(255,255,255,0.02));
            border: 1px solid rgba(126, 166, 235, 0.12);
            border-radius: 18px;
            padding: 16px;
            box-shadow: var(--shadow-md);
            transition: transform 0.16s ease, box-shadow 0.16s ease;
        }

        .group-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 18px 30px rgba(0,0,0,0.20);
        }

        .group-card h4 {
            margin: 0 0 6px;
            font-size: 16px;
        }

        .group-card .count {
            font-size: 30px;
            font-weight: 900;
            letter-spacing: -0.04em;
            margin-bottom: 6px;
        }

        .small-muted {
            color: var(--muted);
            font-size: 12px;
            line-height: 1.5;
        }

        .grouped-sections {
            display: grid;
            gap: 16px;
        }

        .group-section {
            background:
                linear-gradient(180deg, rgba(255,255,255,0.05), rgba(255,255,255,0.03));
            border: 1px solid rgba(127, 167, 237, 0.12);
            border-radius: 22px;
            padding: 18px;
            box-shadow: var(--shadow-md);
        }

        .group-section-header {
            display: flex;
            justify-content: space-between;
            gap: 16px;
            align-items: start;
            margin-bottom: 14px;
        }

        .group-section-title {
            margin: 0;
            font-size: 18px;
            letter-spacing: -0.02em;
        }

        .group-section-sub {
            margin-top: 6px;
            color: var(--muted);
            font-size: 13px;
        }

        .severity-row {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }

        .pill-row {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }

        .pill {
            padding: 8px 11px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 700;
            color: #deecff;
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(128,168,240,0.12);
        }

        .finding-list {
            display: grid;
            gap: 12px;
        }

        .finding {
            background:
                linear-gradient(180deg, rgba(8, 14, 26, 0.92), rgba(10, 17, 30, 0.92));
            border: 1px solid rgba(122, 161, 227, 0.12);
            border-radius: 18px;
            padding: 16px;
            transition: border-color 0.16s ease, transform 0.16s ease, box-shadow 0.16s ease;
        }

        .finding:hover {
            transform: translateY(-2px);
            border-color: rgba(122,161,227,0.20);
            box-shadow: 0 16px 28px rgba(0,0,0,0.18);
        }

        .finding-top {
            display: flex;
            justify-content: space-between;
            gap: 12px;
            align-items: start;
            margin-bottom: 8px;
        }

        .finding h4 {
            margin: 0;
            font-size: 15px;
            line-height: 1.5;
        }

        .finding-block {
            margin-top: 10px;
            color: #dce8fb;
            font-size: 14px;
            line-height: 1.7;
        }

        .finding-label {
            color: #bdd3f5;
            font-weight: 800;
        }

        .penalty-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 12px;
        }

        .downloads {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }

        .download-btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 11px 15px;
            border-radius: 14px;
            font-size: 13px;
            font-weight: 800;
            color: #ecf5ff;
            border: 1px solid rgba(132,174,255,0.14);
            background:
                linear-gradient(180deg, rgba(255,255,255,0.05), rgba(255,255,255,0.03));
            box-shadow:
                inset 0 1px 0 rgba(255,255,255,0.05),
                0 12px 22px rgba(0,0,0,0.16);
            transition: transform 0.16s ease, box-shadow 0.16s ease, border-color 0.16s ease;
        }

        .download-btn:hover {
            transform: translateY(-2px);
            border-color: rgba(132,174,255,0.24);
            box-shadow:
                inset 0 1px 0 rgba(255,255,255,0.05),
                0 14px 28px rgba(0,0,0,0.18),
                0 0 22px rgba(110,181,255,0.10);
        }

        .ranking-grid {
            display: grid;
            gap: 14px;
        }

        .ranking-card {
            background:
                linear-gradient(180deg, rgba(255,255,255,0.05), rgba(255,255,255,0.03));
            border: 1px solid rgba(128,168,240,0.12);
            border-radius: 22px;
            padding: 20px;
            box-shadow: var(--shadow-md);
        }

        .ranking-head {
            display: flex;
            justify-content: space-between;
            gap: 14px;
            align-items: start;
            margin-bottom: 12px;
        }

        .ranking-rank {
            font-size: 12px;
            color: #bfd6f7;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            font-weight: 900;
        }

        .ranking-card h3 {
            margin: 6px 0 0;
            font-size: 22px;
            letter-spacing: -0.02em;
        }

        .ranking-score {
            text-align: right;
        }

        .ranking-score .value {
            font-size: 34px;
            font-weight: 900;
            letter-spacing: -0.04em;
        }

        .ranking-layout {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 14px;
            margin-top: 14px;
        }

        .mini-panel {
            background:
                linear-gradient(180deg, rgba(8,14,26,0.86), rgba(11,18,31,0.90));
            border: 1px solid rgba(123,162,229,0.12);
            border-radius: 18px;
            padding: 14px;
        }

        .mini-panel h4 {
            margin: 0 0 8px;
            font-size: 14px;
        }

        .top-issue-list {
            display: grid;
            gap: 10px;
        }

        .top-issue-item {
            border-top: 1px solid rgba(255,255,255,0.06);
            padding-top: 10px;
        }

        .top-issue-item:first-child {
            border-top: 0;
            padding-top: 0;
        }

        .empty-state {
            background:
                linear-gradient(180deg, rgba(255,255,255,0.04), rgba(255,255,255,0.02));
            border: 1px dashed rgba(130,171,255,0.20);
            border-radius: 20px;
            padding: 30px;
            color: var(--muted);
            text-align: center;
            line-height: 1.7;
        }

        .subtle-stat-line {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-top: 10px;
        }

        .stat-pill {
            padding: 8px 10px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 700;
            color: #dbecff;
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(130,171,255,0.12);
        }

        @media (max-width: 1240px) {
            .main-grid {
                grid-template-columns: 1fr;
            }

            .hero-grid {
                grid-template-columns: 1fr;
            }

            .metric-grid,
            .issues-grid,
            .group-grid,
            .penalty-grid,
            .ranking-layout,
            .summary-strip {
                grid-template-columns: 1fr 1fr;
            }
        }

        @media (max-width: 820px) {
            .app-shell {
                width: min(100% - 20px, 100%);
            }

            .topbar {
                top: 10px;
            }

            .topbar-inner {
                flex-direction: column;
                align-items: start;
            }

            .hero {
                padding: 24px;
            }

            .hero h1 {
                font-size: 38px;
            }

            .metric-grid,
            .issues-grid,
            .group-grid,
            .penalty-grid,
            .ranking-layout,
            .summary-strip,
            .inline-grid-2 {
                grid-template-columns: 1fr;
            }

            .group-section-header,
            .ranking-head,
            .finding-top {
                flex-direction: column;
            }

            .ranking-score {
                text-align: left;
            }
        }
    </style>
</head>
<body>
    {% macro chip_class(severity) -%}
        {%- set s = (severity or "low")|lower -%}
        {%- if s == "critical" -%}chip-critical
        {%- elif s == "high" -%}chip-high
        {%- elif s == "medium" -%}chip-medium
        {%- else -%}chip-low
        {%- endif -%}
    {%- endmacro %}

    {% macro score_band_class(score) -%}
        {%- if score >= 8.5 -%}score-band-excellent
        {%- elif score >= 7.0 -%}score-band-good
        {%- elif score >= 5.0 -%}score-band-watch
        {%- else -%}score-band-risk
        {%- endif -%}
    {%- endmacro %}

    {% macro score_band_label(score) -%}
        {%- if score >= 8.5 -%}Strong engineering position
        {%- elif score >= 7.0 -%}Good with targeted issues
        {%- elif score >= 5.0 -%}Needs review before release
        {%- else -%}High engineering risk
        {%- endif -%}
    {%- endmacro %}

    {% macro download_href(item) -%}
        {%- if item.run_dir is defined and item.filename is defined -%}
            {{ url_for('download_file', run_dir=item.run_dir, filename=item.filename) }}
        {%- elif item.url is defined -%}
            {{ item.url }}
        {%- else -%}
            #
        {%- endif -%}
    {%- endmacro %}

    <div class="app-shell">
        <div class="topbar">
            <div class="topbar-inner">
                <div class="brand-wrap">
                    <div class="brand-mark"></div>
                    <div class="brand-copy">
                        <div class="brand-title">Silicore</div>
                        <div class="brand-sub">Hardware design intelligence</div>
                    </div>
                </div>

                <div class="topbar-badges">
                    <div class="top-badge">Board Review</div>
                    <div class="top-badge">Project Ranking</div>
                    <div class="top-badge">Config Tuning</div>
                    <div class="top-badge">Export Reports</div>
                </div>
            </div>
        </div>

        <section class="hero">
            <div class="hero-grid">
                <div>
                    <div class="hero-eyebrow">Milestone 15 · Product Layer</div>
                    <h1>PCB design review that looks like a real product.</h1>
                    <p>
                        Silicore turns engineering findings into a polished review experience with cleaner board scoring,
                        stronger issue prioritization, grouped risk analysis, project-wide comparisons, and exportable reports
                        that feel closer to something a real customer or company would use.
                    </p>
                    <div class="hero-chip-row">
                        <div class="hero-chip">Premium dashboard styling</div>
                        <div class="hero-chip">Top issue prioritization</div>
                        <div class="hero-chip">Board health summaries</div>
                        <div class="hero-chip">Project ranking UX</div>
                    </div>
                </div>

                <div class="hero-status-card">
                    <div class="status-kicker">Current system status</div>
                    <div class="status-number">Stable</div>
                    <div class="status-copy">
                        Your engine and dashboard flow are now stable enough to focus on visual polish, product perception,
                        and a more premium user experience.
                    </div>
                    <div class="subtle-stat-line">
                        <div class="stat-pill">CLI working</div>
                        <div class="stat-pill">Dashboard working</div>
                        <div class="stat-pill">Exports working</div>
                    </div>
                </div>
            </div>
        </section>

        {% with messages = get_flashed_messages() %}
            {% if messages %}
                <div class="flash-stack">
                    {% for message in messages %}
                        <div class="flash">{{ message }}</div>
                    {% endfor %}
                </div>
            {% endif %}
        {% endwith %}

        <div class="main-grid">
            <aside class="sidebar">
                <section class="card">
                    <div class="card-header">
                        <h2 class="section-title">Single Board Analysis</h2>
                        <p class="section-copy">
                            Upload one board file to generate score, executive summary, grouped risks, top issues,
                            and downloadable exports.
                        </p>
                    </div>
                    <div class="card-body">
                        <div class="divider"></div>
                        <form action="{{ url_for('analyze_board_route') }}" method="post" enctype="multipart/form-data">
                            <label>
                                Board File
                                <input type="file" name="board_file" required>
                            </label>
                            <button class="btn btn-primary" type="submit">Analyze Board</button>
                        </form>
                    </div>
                </section>

                <section class="card">
                    <div class="card-header">
                        <h2 class="section-title">Project Analysis</h2>
                        <p class="section-copy">
                            Upload multiple boards to compare design quality, rank them, and quickly see which boards deserve the most attention.
                        </p>
                    </div>
                    <div class="card-body">
                        <div class="divider"></div>
                        <form action="{{ url_for('analyze_project_route') }}" method="post" enctype="multipart/form-data">
                            <label>
                                Project Files
                                <input type="file" name="project_files" multiple required>
                            </label>
                            <button class="btn btn-primary" type="submit">Analyze Project</button>
                        </form>
                    </div>
                </section>

                <section class="card">
                    <div class="card-header">
                        <h2 class="section-title">Config Editor</h2>
                        <p class="section-copy">
                            Adjust dashboard-facing thresholds while preserving broader config compatibility.
                        </p>
                    </div>
                    <div class="card-body">
                        <div class="divider"></div>
                        <form action="{{ url_for('save_config_route') }}" method="post">
                            <div class="stack">
                                <div>
                                    <div class="minor-title">Layout</div>
                                    <p class="section-copy">Controls spacing and density assumptions.</p>
                                </div>

                                <div class="inline-grid-2">
                                    <label>
                                        Min Component Spacing
                                        <input
                                            type="number"
                                            step="0.01"
                                            name="layout_min_component_spacing"
                                            value="{{ editable_config.layout.min_component_spacing if editable_config and editable_config.layout else '' }}"
                                        >
                                    </label>
                                    <label>
                                        Density Threshold
                                        <input
                                            type="number"
                                            step="0.01"
                                            name="layout_density_threshold"
                                            value="{{ editable_config.layout.density_threshold if editable_config and editable_config.layout else '' }}"
                                        >
                                    </label>
                                </div>

                                <div>
                                    <div class="minor-title">Power</div>
                                    <p class="section-copy">Define required rails and grounding expectations.</p>
                                </div>

                                <label>
                                    Required Power Nets
                                    <input
                                        type="text"
                                        name="power_required_power_nets"
                                        value="{{ editable_config.power.required_power_nets if editable_config and editable_config.power else '' }}"
                                        placeholder="VIN, 3V3, 5V"
                                    >
                                </label>

                                <label>
                                    Required Ground Nets
                                    <input
                                        type="text"
                                        name="power_required_ground_nets"
                                        value="{{ editable_config.power.required_ground_nets if editable_config and editable_config.power else '' }}"
                                        placeholder="GND, AGND"
                                    >
                                </label>

                                <div>
                                    <div class="minor-title">Signal</div>
                                    <p class="section-copy">Set routing expectations and critical net handling.</p>
                                </div>

                                <div class="inline-grid-2">
                                    <label>
                                        Max Trace Length
                                        <input
                                            type="number"
                                            step="0.01"
                                            name="signal_max_trace_length"
                                            value="{{ editable_config.signal.max_trace_length if editable_config and editable_config.signal else '' }}"
                                        >
                                    </label>
                                    <label>
                                        Critical Nets
                                        <input
                                            type="text"
                                            name="signal_critical_nets"
                                            value="{{ editable_config.signal.critical_nets if editable_config and editable_config.signal else '' }}"
                                            placeholder="CLK, USB_D+, USB_D-"
                                        >
                                    </label>
                                </div>

                                <button class="btn btn-secondary" type="submit">Save Config</button>

                                <div class="mini-note">
                                    This editor is designed for practical tuning from the dashboard while keeping the main config usable by the rest of Silicore.
                                </div>
                            </div>
                        </form>
                    </div>
                </section>

                <section class="card">
                    <div class="card-header">
                        <h2 class="section-title">Recent Saved Runs</h2>
                        <p class="section-copy">
                            Review recent single-board and project-level dashboard outputs.
                        </p>
                    </div>
                    <div class="card-body">
                        <div class="divider"></div>
                        {% if recent_runs %}
                            <div class="runs-list">
                                {% for run in recent_runs %}
                                    <div class="run-item">
                                        <p class="run-title">{{ run.name }}</p>
                                        <div class="run-meta">
                                            Type: {{ run.run_type }}<br>
                                            Created: {{ run.created_at }}
                                        </div>
                                    </div>
                                {% endfor %}
                            </div>
                        {% else %}
                            <div class="empty-state">No saved runs yet.</div>
                        {% endif %}
                    </div>
                </section>
            </aside>

            <main class="content">
                {% if result %}
                    <section class="card">
                        <div class="card-header">
                            <h2 class="section-title">Single Board Review</h2>
                            <p class="section-copy">
                                A cleaner engineering review flow that puts health, top issues, and grouped findings first.
                            </p>
                        </div>
                        <div class="card-body result-shell">
                            <div class="metric-grid">
                                <div class="metric-card">
                                    <div class="metric-label">Silicore Risk Score</div>
                                    <div class="metric-value {{ score_band_class(result.score) }}">{{ result.score }}</div>
                                    <div class="metric-sub">{{ score_band_label(result.score) }}</div>
                                </div>

                                <div class="metric-card">
                                    <div class="metric-label">Components</div>
                                    <div class="metric-value">{{ result.board_summary.component_count if result.board_summary else 0 }}</div>
                                    <div class="metric-sub">Parsed component count</div>
                                </div>

                                <div class="metric-card">
                                    <div class="metric-label">Nets</div>
                                    <div class="metric-value">{{ result.board_summary.net_count if result.board_summary else 0 }}</div>
                                    <div class="metric-sub">Detected connectivity entities</div>
                                </div>

                                <div class="metric-card">
                                    <div class="metric-label">Risk Count</div>
                                    <div class="metric-value">{{ result.board_summary.risk_count if result.board_summary else (result.risks|length if result.risks else 0) }}</div>
                                    <div class="metric-sub">Current ruleset findings</div>
                                </div>
                            </div>

                            <div class="summary-strip">
                                <div class="summary-panel">
                                    <h3>{{ result.health_summary.title }}</h3>
                                    <p>{{ result.health_summary.summary }}</p>
                                </div>

                                <div class="summary-panel">
                                    <h3>Executive Summary</h3>
                                    <p>
                                        {% if result.executive_summary and result.executive_summary.summary %}
                                            {{ result.executive_summary.summary }}
                                        {% else %}
                                            No executive summary available for this board yet.
                                        {% endif %}
                                    </p>
                                </div>
                            </div>

                            <section>
                                <div class="section-block-header">
                                    <div>
                                        <h3 class="section-title">Top Issues</h3>
                                        <div class="copy">Highest-priority findings to review first.</div>
                                    </div>
                                </div>

                                {% if result.top_issues %}
                                    <div class="issues-grid">
                                        {% for issue in result.top_issues %}
                                            <div class="issue-card">
                                                <div class="chip {{ chip_class(issue.severity) }}">{{ issue.severity }}</div>
                                                <h4>{{ issue.message }}</h4>
                                                <div class="issue-meta">Category: {{ issue.category }}</div>

                                                {% if issue.recommendation %}
                                                    <div class="finding-block">
                                                        <span class="finding-label">Recommendation:</span>
                                                        {{ issue.recommendation }}
                                                    </div>
                                                {% endif %}
                                            </div>
                                        {% endfor %}
                                    </div>
                                {% else %}
                                    <div class="empty-state">No issues found.</div>
                                {% endif %}
                            </section>

                            <section>
                                <div class="section-block-header">
                                    <div>
                                        <h3 class="section-title">Category Summary</h3>
                                        <div class="copy">Quick grouped counts by engineering section.</div>
                                    </div>
                                </div>

                                {% if result.grouped_risks %}
                                    <div class="group-grid">
                                        {% for section in result.grouped_risks %}
                                            <div class="group-card">
                                                <h4>{{ section.title }}</h4>
                                                <div class="count">{{ section.count }}</div>
                                                <div class="small-muted">
                                                    issue{% if section.count != 1 %}s{% endif %}
                                                </div>
                                            </div>
                                        {% endfor %}
                                    </div>
                                {% else %}
                                    <div class="empty-state">No grouped findings.</div>
                                {% endif %}
                            </section>

                            {% if result.score_explanation %}
                                <section>
                                    <div class="section-block-header">
                                        <div>
                                            <h3 class="section-title">Score Breakdown</h3>
                                            <div class="copy">Where score was removed and why.</div>
                                        </div>
                                    </div>

                                    <div class="penalty-grid">
                                        <div class="metric-card">
                                            <div class="metric-label">Start</div>
                                            <div class="metric-value">{{ result.score_explanation.start_score }}</div>
                                        </div>

                                        <div class="metric-card">
                                            <div class="metric-label">Total Penalty</div>
                                            <div class="metric-value">{{ result.score_explanation.total_penalty }}</div>
                                        </div>

                                        <div class="metric-card" style="grid-column: span 2;">
                                            <div class="metric-label">Severity Penalties</div>
                                            <div class="pill-row">
                                                {% if result.score_explanation.severity_totals %}
                                                    {% for severity, penalty in result.score_explanation.severity_totals.items() %}
                                                        <div class="pill">{{ severity }}: {{ penalty }}</div>
                                                    {% endfor %}
                                                {% else %}
                                                    <div class="pill">None</div>
                                                {% endif %}
                                            </div>
                                        </div>

                                        <div class="metric-card" style="grid-column: 1 / -1;">
                                            <div class="metric-label">Category Penalties</div>
                                            <div class="pill-row">
                                                {% if result.score_explanation.category_totals %}
                                                    {% for category, penalty in result.score_explanation.category_totals.items() %}
                                                        <div class="pill">{{ category }}: {{ penalty }}</div>
                                                    {% endfor %}
                                                {% else %}
                                                    <div class="pill">No category penalties recorded</div>
                                                {% endif %}
                                            </div>
                                        </div>
                                    </div>
                                </section>
                            {% endif %}

                            <section>
                                <div class="section-block-header">
                                    <div>
                                        <h3 class="section-title">Grouped Findings</h3>
                                        <div class="copy">Organized by engineering category for easier review flow.</div>
                                    </div>
                                </div>

                                {% if result.grouped_risks %}
                                    <div class="grouped-sections">
                                        {% for section in result.grouped_risks %}
                                            <div class="group-section">
                                                <div class="group-section-header">
                                                    <div>
                                                        <h4 class="group-section-title">{{ section.title }}</h4>
                                                        <div class="group-section-sub">
                                                            {{ section.count }} finding{% if section.count != 1 %}s{% endif %} in this category
                                                        </div>
                                                    </div>

                                                    <div class="severity-row">
                                                        {% if section.severity_counts.critical %}
                                                            <div class="pill">critical: {{ section.severity_counts.critical }}</div>
                                                        {% endif %}
                                                        {% if section.severity_counts.high %}
                                                            <div class="pill">high: {{ section.severity_counts.high }}</div>
                                                        {% endif %}
                                                        {% if section.severity_counts.medium %}
                                                            <div class="pill">medium: {{ section.severity_counts.medium }}</div>
                                                        {% endif %}
                                                        {% if section.severity_counts.low %}
                                                            <div class="pill">low: {{ section.severity_counts.low }}</div>
                                                        {% endif %}
                                                    </div>
                                                </div>

                                                <div class="finding-list">
                                                    {% for risk in section.risks %}
                                                        <div class="finding">
                                                            <div class="finding-top">
                                                                <div>
                                                                    <div class="chip {{ chip_class(risk.severity) }}">{{ risk.severity }}</div>
                                                                    <h4>{{ risk.message }}</h4>
                                                                </div>

                                                                <div class="small-muted">
                                                                    {% if risk.rule_id %}Rule: {{ risk.rule_id }}{% else %}Grouped finding{% endif %}
                                                                </div>
                                                            </div>

                                                            <div class="finding-block">
                                                                <span class="finding-label">Recommendation:</span>
                                                                {{ risk.recommendation if risk.recommendation else "Manual review recommended." }}
                                                            </div>

                                                            {% if risk.explanation %}
                                                                <div class="finding-block">
                                                                    <span class="finding-label">Explanation:</span><br>
                                                                    {% if risk.explanation.root_cause %}Root cause: {{ risk.explanation.root_cause }}<br>{% endif %}
                                                                    {% if risk.explanation.impact %}Impact: {{ risk.explanation.impact }}<br>{% endif %}
                                                                    {% if risk.explanation.confidence %}Confidence: {{ risk.explanation.confidence }}{% endif %}
                                                                </div>
                                                            {% endif %}

                                                            {% if risk.components or risk.nets or risk.region %}
                                                                <div class="finding-block">
                                                                    {% if risk.components %}
                                                                        <span class="finding-label">Components:</span> {{ risk.components | join(", ") }}<br>
                                                                    {% endif %}
                                                                    {% if risk.nets %}
                                                                        <span class="finding-label">Nets:</span> {{ risk.nets | join(", ") }}<br>
                                                                    {% endif %}
                                                                    {% if risk.region %}
                                                                        <span class="finding-label">Region:</span> {{ risk.region }}
                                                                    {% endif %}
                                                                </div>
                                                            {% endif %}
                                                        </div>
                                                    {% endfor %}
                                                </div>
                                            </div>
                                        {% endfor %}
                                    </div>
                                {% else %}
                                    <div class="empty-state">
                                        <strong>No risks detected</strong><br><br>
                                        This board did not produce any findings in the current ruleset and config state.
                                    </div>
                                {% endif %}
                            </section>

                            {% if result.downloads %}
                                <section>
                                    <div class="section-block-header">
                                        <div>
                                            <h3 class="section-title">Exports</h3>
                                            <div class="copy">Download generated outputs for review and sharing.</div>
                                        </div>
                                    </div>

                                    <div class="downloads">
                                        {% for item in result.downloads %}
                                            <a class="download-btn" href="{{ download_href(item) }}">{{ item.label }}</a>
                                        {% endfor %}
                                    </div>
                                </section>
                            {% endif %}
                        </div>
                    </section>
                {% endif %}

                {% if project_result %}
                    <section class="card">
                        <div class="card-header">
                            <h2 class="section-title">Project Ranking Review</h2>
                            <p class="section-copy">
                                Compare boards across the uploaded project set and quickly see which designs are strongest and weakest.
                            </p>
                        </div>

                        <div class="card-body result-shell">
                            {% if project_result.project_summary %}
                                <div class="metric-grid">
                                    <div class="metric-card">
                                        <div class="metric-label">Boards</div>
                                        <div class="metric-value">{{ project_result.project_summary.total_boards }}</div>
                                        <div class="metric-sub">Uploaded project set</div>
                                    </div>

                                    <div class="metric-card">
                                        <div class="metric-label">Average Score</div>
                                        <div class="metric-value">{{ project_result.project_summary.average_score }}</div>
                                        <div class="metric-sub">Mean board quality</div>
                                    </div>

                                    <div class="metric-card">
                                        <div class="metric-label">Best Score</div>
                                        <div class="metric-value">{{ project_result.project_summary.best_score }}</div>
                                        <div class="metric-sub">Top current design</div>
                                    </div>

                                    <div class="metric-card">
                                        <div class="metric-label">Worst Score</div>
                                        <div class="metric-value">{{ project_result.project_summary.worst_score }}</div>
                                        <div class="metric-sub">Board needing most attention</div>
                                    </div>
                                </div>
                            {% endif %}

                            <div class="summary-strip">
                                <div class="summary-panel">
                                    <h3>{{ project_result.project_health_summary.title if project_result.project_health_summary else "Project Health" }}</h3>
                                    <p>
                                        {{ project_result.project_health_summary.summary if project_result.project_health_summary else "No project health summary available." }}
                                    </p>
                                </div>

                                <div class="summary-panel">
                                    <h3>Project Insight</h3>
                                    <p>
                                        {% if project_result.project_insight and project_result.project_insight.summary %}
                                            {{ project_result.project_insight.summary }}
                                        {% else %}
                                            No project insight summary available yet.
                                        {% endif %}
                                    </p>
                                </div>
                            </div>

                            <section>
                                <div class="section-block-header">
                                    <div>
                                        <h3 class="section-title">Ranked Boards</h3>
                                        <div class="copy">A product-style comparison of the uploaded board set.</div>
                                    </div>
                                </div>

                                {% if project_result.boards %}
                                    <div class="ranking-grid">
                                        {% for board in project_result.boards %}
                                            <div class="ranking-card">
                                                <div class="ranking-head">
                                                    <div>
                                                        <div class="ranking-rank">
                                                            #{{ board.rank }}
                                                            {% if board.rank == 1 %}
                                                                · Top ranked board
                                                            {% elif board.rank == project_result.boards|length %}
                                                                · Lowest ranked board
                                                            {% else %}
                                                                · Project board
                                                            {% endif %}
                                                        </div>
                                                        <h3>{{ board.filename }}</h3>
                                                    </div>

                                                    <div class="ranking-score">
                                                        <div class="value {{ score_band_class(board.score) }}">{{ board.score }}</div>
                                                        <div class="small-muted">{{ score_band_label(board.score) }}</div>
                                                    </div>
                                                </div>

                                                <div class="ranking-layout">
                                                    <div class="mini-panel">
                                                        <h4>{{ board.health_summary.title }}</h4>
                                                        <div class="small-muted">{{ board.health_summary.summary }}</div>
                                                    </div>

                                                    <div class="mini-panel">
                                                        <h4>Top Issues</h4>
                                                        {% if board.top_issues %}
                                                            <div class="top-issue-list">
                                                                {% for risk in board.top_issues %}
                                                                    <div class="top-issue-item">
                                                                        <div class="chip {{ chip_class(risk.severity) }}">{{ risk.severity }}</div>
                                                                        <div style="font-size:13px; line-height:1.55;">{{ risk.message }}</div>
                                                                    </div>
                                                                {% endfor %}
                                                            </div>
                                                        {% else %}
                                                            <div class="small-muted">No top issues recorded.</div>
                                                        {% endif %}
                                                    </div>
                                                </div>
                                            </div>
                                        {% endfor %}
                                    </div>
                                {% else %}
                                    <div class="empty-state">No project boards analyzed.</div>
                                {% endif %}
                            </section>

                            {% if project_result.downloads %}
                                <section>
                                    <div class="section-block-header">
                                        <div>
                                            <h3 class="section-title">Project Exports</h3>
                                            <div class="copy">Download the full project outputs.</div>
                                        </div>
                                    </div>

                                    <div class="downloads">
                                        {% for item in project_result.downloads %}
                                            <a class="download-btn" href="{{ download_href(item) }}">{{ item.label }}</a>
                                        {% endfor %}
                                    </div>
                                </section>
                            {% endif %}
                        </div>
                    </section>
                {% endif %}

                {% if not result and not project_result %}
                    <section class="card">
                        <div class="card-body">
                            <div class="empty-state">
                                <strong>No analysis loaded yet.</strong><br><br>
                                Upload a board file for single-board review or upload multiple files for project ranking.
                            </div>
                        </div>
                    </section>
                {% endif %}
            </main>
        </div>
    </div>
</body>
</html>
"""


def _render_dashboard(result=None, project_result=None):
    _, editable_config = get_dashboard_config(CONFIG_PATH)
    recent_runs = get_recent_runs(RUNS_FOLDER)[:5]

    return render_template_string(
        HTML_TEMPLATE,
        result=result,
        project_result=project_result,
        editable_config=editable_config,
        recent_runs=recent_runs,
    )


@app.route("/", methods=["GET"])
def index():
    return _render_dashboard()


@app.route("/analyze-board", methods=["POST"])
def analyze_board_route():
    board_file = request.files.get("board_file")

    try:
        response = analyze_single_board(
            uploaded_file=board_file,
            upload_folder=UPLOAD_FOLDER,
            runs_folder=RUNS_FOLDER,
            config_path=CONFIG_PATH,
        )
        result = response.get("result")
        result = _enrich_single_result(result or {})
        return _render_dashboard(result=result)
    except Exception as exc:
        flash(f"Board analysis failed: {exc}")
        return redirect(url_for("index"))


@app.route("/analyze-project", methods=["POST"])
def analyze_project_route():
    project_files = request.files.getlist("project_files")

    try:
        response = analyze_project_files(
            uploaded_files=project_files,
            upload_folder=UPLOAD_FOLDER,
            runs_folder=RUNS_FOLDER,
            config_path=CONFIG_PATH,
        )
        project_result = response.get("project_result", {})
        project_result["project_summary"] = project_result.get("summary", {})
        project_result = _enrich_project_result(project_result)
        return _render_dashboard(project_result=project_result)
    except Exception as exc:
        flash(f"Project analysis failed: {exc}")
        return redirect(url_for("index"))


@app.route("/save-config", methods=["POST"])
def save_config_route():
    try:
        current_config, _ = get_dashboard_config(CONFIG_PATH)
        updated_fields = parse_config_form(request.form)
        save_config(CONFIG_PATH, current_config, updated_fields)
        flash("Config saved successfully.")
    except Exception as exc:
        flash(f"Config save failed: {exc}")

    return redirect(url_for("index"))


@app.route("/download/<run_dir>/<filename>", methods=["GET"])
def download_file(run_dir, filename):
    directory = os.path.join(RUNS_FOLDER, run_dir)
    return send_from_directory(directory, filename, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)