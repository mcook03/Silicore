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
                [_severity_rank(risk.get("severity")) for risk in section["risks"]]
                or [99]
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

    return project_result


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Silicore Dashboard</title>
    <style>
        :root {
            --bg: #0b1020;
            --bg-elevated: #141b2d;
            --bg-soft: #1a2238;
            --card: #12192b;
            --card-2: #18233d;
            --text: #e8edf7;
            --muted: #aab6d3;
            --border: rgba(255, 255, 255, 0.08);
            --accent: #6ea8fe;
            --accent-2: #7ef0c5;
            --danger: #ff6b6b;
            --warning: #ffcc66;
            --success: #5dd39e;
            --critical: #ff4d6d;
            --shadow: 0 20px 50px rgba(0, 0, 0, 0.28);
            --radius-xl: 22px;
            --radius-lg: 18px;
            --radius-md: 14px;
            --radius-sm: 10px;
        }

        * {
            box-sizing: border-box;
        }

        html, body {
            margin: 0;
            padding: 0;
            background:
                radial-gradient(circle at top left, rgba(110, 168, 254, 0.15), transparent 28%),
                radial-gradient(circle at top right, rgba(126, 240, 197, 0.10), transparent 30%),
                linear-gradient(180deg, #0a0f1d 0%, #0b1020 100%);
            color: var(--text);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Inter, Helvetica, Arial, sans-serif;
        }

        a {
            color: var(--accent);
            text-decoration: none;
        }

        a:hover {
            text-decoration: underline;
        }

        .page {
            width: min(1440px, calc(100% - 32px));
            margin: 24px auto 48px;
        }

        .hero {
            background: linear-gradient(135deg, rgba(19, 30, 54, 0.95), rgba(12, 18, 32, 0.95));
            border: 1px solid var(--border);
            border-radius: var(--radius-xl);
            padding: 28px;
            box-shadow: var(--shadow);
            display: grid;
            grid-template-columns: 1.4fr 1fr;
            gap: 20px;
        }

        .hero-title {
            font-size: 38px;
            line-height: 1.05;
            margin: 0 0 10px;
            letter-spacing: -0.03em;
        }

        .hero-subtitle {
            color: var(--muted);
            font-size: 16px;
            line-height: 1.7;
            margin: 0;
            max-width: 820px;
        }

        .hero-badges {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 18px;
        }

        .badge {
            padding: 8px 12px;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border);
            color: var(--text);
            font-size: 13px;
            font-weight: 600;
            letter-spacing: 0.01em;
        }

        .hero-side {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 12px;
            align-content: start;
        }

        .mini-stat {
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            padding: 16px;
        }

        .mini-stat-label {
            font-size: 12px;
            color: var(--muted);
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 8px;
        }

        .mini-stat-value {
            font-size: 22px;
            font-weight: 700;
        }

        .flash-stack {
            margin-top: 18px;
            display: grid;
            gap: 10px;
        }

        .flash {
            border-radius: var(--radius-md);
            padding: 14px 16px;
            border: 1px solid var(--border);
            background: rgba(255, 255, 255, 0.05);
            color: var(--text);
        }

        .layout {
            display: grid;
            grid-template-columns: 400px minmax(0, 1fr);
            gap: 20px;
            margin-top: 20px;
            align-items: start;
        }

        .left-column,
        .right-column {
            display: grid;
            gap: 20px;
        }

        .panel {
            background: linear-gradient(180deg, rgba(20, 27, 45, 0.98), rgba(14, 20, 34, 0.98));
            border: 1px solid var(--border);
            border-radius: var(--radius-xl);
            padding: 22px;
            box-shadow: var(--shadow);
        }

        .panel h2 {
            margin: 0 0 8px;
            font-size: 22px;
            letter-spacing: -0.02em;
        }

        .panel p.section-copy {
            margin: 0 0 18px;
            color: var(--muted);
            line-height: 1.65;
            font-size: 14px;
        }

        .stack {
            display: grid;
            gap: 14px;
        }

        .field-group {
            display: grid;
            gap: 8px;
        }

        .field-group label {
            font-size: 13px;
            font-weight: 600;
            color: var(--text);
        }

        input[type="text"],
        input[type="number"],
        input[type="file"] {
            width: 100%;
            border: 1px solid var(--border);
            background: var(--bg-soft);
            color: var(--text);
            border-radius: 12px;
            padding: 12px 14px;
            font-size: 14px;
            outline: none;
        }

        input[type="file"] {
            padding: 10px 12px;
        }

        input:focus {
            border-color: rgba(110, 168, 254, 0.7);
            box-shadow: 0 0 0 3px rgba(110, 168, 254, 0.12);
        }

        .form-card {
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            padding: 16px;
            background: rgba(255, 255, 255, 0.03);
        }

        .form-card-title {
            margin: 0 0 6px;
            font-size: 15px;
            font-weight: 700;
        }

        .form-card-copy {
            margin: 0 0 14px;
            color: var(--muted);
            font-size: 13px;
            line-height: 1.6;
        }

        .btn {
            border: 0;
            border-radius: 12px;
            padding: 12px 16px;
            font-size: 14px;
            font-weight: 700;
            cursor: pointer;
            transition: transform 0.15s ease, opacity 0.15s ease;
        }

        .btn:hover {
            transform: translateY(-1px);
            opacity: 0.96;
        }

        .btn-primary {
            background: linear-gradient(135deg, var(--accent), #98bfff);
            color: #09101f;
        }

        .btn-secondary {
            background: linear-gradient(135deg, var(--accent-2), #b4ffe5);
            color: #082119;
        }

        .btn-muted {
            background: rgba(255, 255, 255, 0.06);
            color: var(--text);
            border: 1px solid var(--border);
        }

        .result-header {
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
            align-items: start;
            gap: 14px;
            margin-bottom: 18px;
        }

        .result-eyebrow {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 7px 11px;
            border-radius: 999px;
            background: rgba(110, 168, 254, 0.12);
            border: 1px solid rgba(110, 168, 254, 0.25);
            color: #cfe0ff;
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }

        .result-title {
            margin: 10px 0 6px;
            font-size: 28px;
            letter-spacing: -0.03em;
        }

        .result-copy {
            margin: 0;
            color: var(--muted);
            font-size: 14px;
            line-height: 1.65;
        }

        .score-card {
            min-width: 220px;
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.06), rgba(255, 255, 255, 0.03));
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            padding: 18px;
        }

        .score-label {
            color: var(--muted);
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 8px;
        }

        .score-value {
            font-size: 42px;
            line-height: 1;
            font-weight: 800;
            letter-spacing: -0.04em;
            margin-bottom: 10px;
        }

        .score-band {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 7px 10px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 700;
            border: 1px solid transparent;
        }

        .score-band-excellent {
            color: #c8ffea;
            background: rgba(93, 211, 158, 0.12);
            border-color: rgba(93, 211, 158, 0.24);
        }

        .score-band-good {
            color: #d8f0ff;
            background: rgba(110, 168, 254, 0.12);
            border-color: rgba(110, 168, 254, 0.24);
        }

        .score-band-watch {
            color: #fff1cc;
            background: rgba(255, 204, 102, 0.12);
            border-color: rgba(255, 204, 102, 0.24);
        }

        .score-band-risk {
            color: #ffd6dd;
            background: rgba(255, 77, 109, 0.12);
            border-color: rgba(255, 77, 109, 0.24);
        }

        .grid-stats {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 12px;
            margin-bottom: 18px;
        }

        .stat-card {
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            padding: 16px;
        }

        .stat-card-label {
            color: var(--muted);
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 8px;
        }

        .stat-card-value {
            font-size: 28px;
            font-weight: 800;
            letter-spacing: -0.03em;
        }

        .section-title {
            margin: 22px 0 12px;
            font-size: 18px;
            letter-spacing: -0.02em;
        }

        .chip-row {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }

        .chip {
            border-radius: 999px;
            padding: 8px 12px;
            font-size: 13px;
            font-weight: 700;
            border: 1px solid var(--border);
            background: rgba(255, 255, 255, 0.05);
        }

        .chip-critical {
            background: rgba(255, 77, 109, 0.14);
            border-color: rgba(255, 77, 109, 0.25);
            color: #ffd6dd;
        }

        .chip-high {
            background: rgba(255, 107, 107, 0.14);
            border-color: rgba(255, 107, 107, 0.25);
            color: #ffdfe1;
        }

        .chip-medium {
            background: rgba(255, 204, 102, 0.14);
            border-color: rgba(255, 204, 102, 0.25);
            color: #fff1cc;
        }

        .chip-low {
            background: rgba(93, 211, 158, 0.14);
            border-color: rgba(93, 211, 158, 0.25);
            color: #d8ffee;
        }

        .finding-list,
        .board-list,
        .run-list {
            display: grid;
            gap: 14px;
        }

        .finding-card,
        .board-card,
        .run-card,
        .category-card,
        .summary-card,
        .top-issue-card {
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            background: rgba(255, 255, 255, 0.035);
            padding: 16px;
        }

        .finding-top,
        .board-top,
        .run-top,
        .category-top {
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
            gap: 12px;
            align-items: start;
        }

        .severity-pill {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            border-radius: 999px;
            padding: 7px 11px;
            font-size: 12px;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            border: 1px solid transparent;
        }

        .severity-critical {
            color: #ffd6dd;
            background: rgba(255, 77, 109, 0.14);
            border-color: rgba(255, 77, 109, 0.24);
        }

        .severity-high {
            color: #ffdfe1;
            background: rgba(255, 107, 107, 0.14);
            border-color: rgba(255, 107, 107, 0.24);
        }

        .severity-medium {
            color: #fff1cc;
            background: rgba(255, 204, 102, 0.14);
            border-color: rgba(255, 204, 102, 0.24);
        }

        .severity-low {
            color: #d8ffee;
            background: rgba(93, 211, 158, 0.14);
            border-color: rgba(93, 211, 158, 0.24);
        }

        .finding-title,
        .board-title,
        .run-title,
        .category-title,
        .summary-title {
            margin: 10px 0 6px;
            font-size: 18px;
            font-weight: 800;
            letter-spacing: -0.02em;
        }

        .finding-subtitle,
        .board-subtitle,
        .run-subtitle,
        .summary-copy,
        .category-subtitle {
            color: var(--muted);
            font-size: 13px;
            line-height: 1.6;
            margin: 0;
        }

        .finding-body {
            margin-top: 14px;
            display: grid;
            gap: 10px;
        }

        .finding-box,
        .top-issue-item {
            border: 1px solid var(--border);
            border-radius: var(--radius-md);
            padding: 12px 14px;
            background: rgba(255, 255, 255, 0.03);
        }

        .finding-box-label {
            color: var(--muted);
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 6px;
        }

        .finding-box-value {
            color: var(--text);
            line-height: 1.65;
            font-size: 14px;
        }

        .meta-row {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 12px;
        }

        .meta-chip {
            padding: 7px 10px;
            border-radius: 999px;
            font-size: 12px;
            color: var(--muted);
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid var(--border);
        }

        .downloads {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 10px;
        }

        .download-link {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            border-radius: 999px;
            padding: 10px 12px;
            background: rgba(110, 168, 254, 0.12);
            border: 1px solid rgba(110, 168, 254, 0.24);
            color: #dce9ff;
            font-weight: 700;
            font-size: 13px;
        }

        .board-rank {
            width: 42px;
            height: 42px;
            border-radius: 14px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            background: rgba(126, 240, 197, 0.12);
            border: 1px solid rgba(126, 240, 197, 0.22);
            color: #d7fff0;
            flex: 0 0 auto;
        }

        .board-score {
            font-size: 24px;
            font-weight: 800;
            letter-spacing: -0.03em;
        }

        .split {
            display: grid;
            grid-template-columns: 1.05fr 0.95fr;
            gap: 16px;
        }

        .split-tight {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
        }

        .muted-note {
            color: var(--muted);
            line-height: 1.65;
            font-size: 14px;
        }

        .footer-note {
            margin-top: 18px;
            color: var(--muted);
            font-size: 13px;
            line-height: 1.7;
        }

        .hidden-compat {
            display: none;
        }

        .rank-label {
            font-size: 12px;
            color: var(--muted);
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }

        @media (max-width: 1120px) {
            .layout,
            .hero,
            .split,
            .split-tight {
                grid-template-columns: 1fr;
            }

            .hero-side,
            .grid-stats {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
        }

        @media (max-width: 720px) {
            .page {
                width: min(100% - 20px, 100%);
                margin: 10px auto 28px;
            }

            .panel,
            .hero {
                padding: 18px;
            }

            .hero-title {
                font-size: 30px;
            }

            .hero-side,
            .grid-stats {
                grid-template-columns: 1fr;
            }

            .score-card {
                width: 100%;
            }
        }
    </style>
</head>
<body>
    {% macro severity_class(severity) -%}
        {%- set s = (severity or "low")|lower -%}
        {%- if s == "critical" -%}severity-critical
        {%- elif s == "high" -%}severity-high
        {%- elif s == "medium" -%}severity-medium
        {%- else -%}severity-low
        {%- endif -%}
    {%- endmacro %}

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

    <div class="page">
        <section class="hero">
            <div>
                <div class="result-eyebrow">Milestone 15 · Phase 2</div>
                <h1 class="hero-title">Silicore</h1>
                <p class="hero-subtitle">
                    Phase 2 upgrades the product layer: grouped findings, top issue summaries, cleaner board review,
                    and stronger ranking presentation while keeping the now-stable analysis engine underneath.
                </p>
                <div class="hero-badges">
                    <span class="badge">Grouped Findings</span>
                    <span class="badge">Top Issues</span>
                    <span class="badge">Board Health Summary</span>
                    <span class="badge">Project Ranking UX</span>
                </div>
            </div>

            <div class="hero-side">
                <div class="mini-stat">
                    <div class="mini-stat-label">Milestone</div>
                    <div class="mini-stat-value">15.2</div>
                </div>
                <div class="mini-stat">
                    <div class="mini-stat-label">Engine state</div>
                    <div class="mini-stat-value">Stable</div>
                </div>
                <div class="mini-stat">
                    <div class="mini-stat-label">Primary goal</div>
                    <div class="mini-stat-value">Review Flow</div>
                </div>
                <div class="mini-stat">
                    <div class="mini-stat-label">Output style</div>
                    <div class="mini-stat-value">Productized</div>
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

        <div class="layout">
            <div class="left-column">
                <section class="panel">
                    <h2>Single Board Analysis</h2>
                    <p class="section-copy">
                        Upload one board file to generate a score, grouped findings, top issues,
                        recommendations, and downloadable exports.
                    </p>
                    <form action="{{ url_for('analyze') }}" method="post" enctype="multipart/form-data" class="stack">
                        <div class="field-group">
                            <label for="single_file">Board File</label>
                            <input id="single_file" name="single_file" type="file" required />
                        </div>
                        <button class="btn btn-primary" type="submit">Analyze Board</button>
                    </form>
                </section>

                <section class="panel">
                    <h2>Project Analysis</h2>
                    <p class="section-copy">
                        Upload multiple files to rank boards, compare health, and surface the strongest and weakest designs.
                    </p>
                    <form action="{{ url_for('analyze_project') }}" method="post" enctype="multipart/form-data" class="stack">
                        <div class="field-group">
                            <label for="project_files">Project Files</label>
                            <input id="project_files" name="project_files" type="file" multiple required />
                        </div>
                        <button class="btn btn-secondary" type="submit">Analyze Project</button>
                    </form>
                </section>

                <section class="panel">
                    <h2>Config Editor</h2>
                    <p class="section-copy">
                        Tune thresholds and net expectations for the dashboard while preserving compatibility with the current config loader.
                    </p>

                    <form action="{{ url_for('save_config_route') }}" method="post" class="stack">
                        <div class="form-card">
                            <div class="form-card-title">Layout</div>
                            <div class="form-card-copy">
                                Controls spacing and density assumptions.
                            </div>

                            <div class="stack">
                                <div class="field-group">
                                    <label for="layout_min_component_spacing">Min Component Spacing</label>
                                    <input
                                        id="layout_min_component_spacing"
                                        name="layout_min_component_spacing"
                                        type="number"
                                        step="any"
                                        value="{{ config.layout.min_component_spacing if config.layout and config.layout.min_component_spacing is not none else '' }}"
                                    />
                                    <input
                                        class="hidden-compat"
                                        name="min_component_spacing"
                                        type="hidden"
                                        value="{{ config.layout.min_component_spacing if config.layout and config.layout.min_component_spacing is not none else '' }}"
                                    />
                                </div>

                                <div class="field-group">
                                    <label for="layout_density_threshold">Density Threshold</label>
                                    <input
                                        id="layout_density_threshold"
                                        name="layout_density_threshold"
                                        type="number"
                                        step="1"
                                        value="{{ config.layout.density_threshold if config.layout and config.layout.density_threshold is not none else '' }}"
                                    />
                                    <input
                                        class="hidden-compat"
                                        name="density_threshold"
                                        type="hidden"
                                        value="{{ config.layout.density_threshold if config.layout and config.layout.density_threshold is not none else '' }}"
                                    />
                                </div>
                            </div>
                        </div>

                        <div class="form-card">
                            <div class="form-card-title">Power</div>
                            <div class="form-card-copy">
                                Define expected power and ground nets.
                            </div>

                            <div class="stack">
                                <div class="field-group">
                                    <label for="power_required_power_nets">Required Power Nets</label>
                                    <input
                                        id="power_required_power_nets"
                                        name="power_required_power_nets"
                                        type="text"
                                        value="{{ (config.power.required_power_nets | join(', ')) if config.power and config.power.required_power_nets else '' }}"
                                    />
                                    <input
                                        class="hidden-compat"
                                        name="required_power_nets"
                                        type="hidden"
                                        value="{{ (config.power.required_power_nets | join(', ')) if config.power and config.power.required_power_nets else '' }}"
                                    />
                                </div>

                                <div class="field-group">
                                    <label for="power_required_ground_nets">Required Ground Nets</label>
                                    <input
                                        id="power_required_ground_nets"
                                        name="power_required_ground_nets"
                                        type="text"
                                        value="{{ (config.power.required_ground_nets | join(', ')) if config.power and config.power.required_ground_nets else '' }}"
                                    />
                                    <input
                                        class="hidden-compat"
                                        name="required_ground_nets"
                                        type="hidden"
                                        value="{{ (config.power.required_ground_nets | join(', ')) if config.power and config.power.required_ground_nets else '' }}"
                                    />
                                </div>
                            </div>
                        </div>

                        <div class="form-card">
                            <div class="form-card-title">Signal</div>
                            <div class="form-card-copy">
                                Set routing assumptions and critical nets.
                            </div>

                            <div class="stack">
                                <div class="field-group">
                                    <label for="signal_max_trace_length">Max Trace Length</label>
                                    <input
                                        id="signal_max_trace_length"
                                        name="signal_max_trace_length"
                                        type="number"
                                        step="any"
                                        value="{{ config.signal.max_trace_length if config.signal and config.signal.max_trace_length is not none else '' }}"
                                    />
                                    <input
                                        class="hidden-compat"
                                        name="max_trace_length"
                                        type="hidden"
                                        value="{{ config.signal.max_trace_length if config.signal and config.signal.max_trace_length is not none else '' }}"
                                    />
                                </div>

                                <div class="field-group">
                                    <label for="signal_critical_nets">Critical Nets</label>
                                    <input
                                        id="signal_critical_nets"
                                        name="signal_critical_nets"
                                        type="text"
                                        value="{{ (config.signal.critical_nets | join(', ')) if config.signal and config.signal.critical_nets else '' }}"
                                    />
                                    <input
                                        class="hidden-compat"
                                        name="critical_nets"
                                        type="hidden"
                                        value="{{ (config.signal.critical_nets | join(', ')) if config.signal and config.signal.critical_nets else '' }}"
                                    />
                                </div>
                            </div>
                        </div>

                        <button class="btn btn-muted" type="submit">Save Config</button>
                    </form>
                </section>

                <section class="panel">
                    <h2>Recent Saved Runs</h2>
                    <p class="section-copy">
                        Review recent dashboard-generated analyses and project exports.
                    </p>

                    {% if recent_runs %}
                        <div class="run-list">
                            {% for run in recent_runs %}
                                <div class="run-card">
                                    <div class="run-top">
                                        <div>
                                            <div class="run-title">{{ run.name }}</div>
                                            <p class="run-subtitle">
                                                Type: {{ run.run_type }}<br />
                                                Created: {{ run.created_at }}
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            {% endfor %}
                        </div>
                    {% else %}
                        <p class="muted-note">No saved runs yet.</p>
                    {% endif %}
                </section>
            </div>

            <div class="right-column">
                {% if result %}
                    <section class="panel">
                        <div class="result-header">
                            <div>
                                <div class="result-eyebrow">Single Board Review</div>
                                <h2 class="result-title">{{ result.filename }}</h2>
                                <p class="result-copy">
                                    This view is organized for engineering review: overall health first, then top issues, then grouped findings by category.
                                </p>
                            </div>

                            <div class="score-card">
                                <div class="score-label">Silicore Risk Score</div>
                                <div class="score-value">{{ result.score }}</div>
                                <div class="score-band {{ score_band_class(result.score) }}">
                                    {{ score_band_label(result.score) }}
                                </div>
                            </div>
                        </div>

                        <div class="grid-stats">
                            <div class="stat-card">
                                <div class="stat-card-label">Components</div>
                                <div class="stat-card-value">
                                    {{ result.board_summary.component_count if result.board_summary else 0 }}
                                </div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-card-label">Nets</div>
                                <div class="stat-card-value">
                                    {{ result.board_summary.net_count if result.board_summary else 0 }}
                                </div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-card-label">Risk Count</div>
                                <div class="stat-card-value">
                                    {{ result.board_summary.risk_count if result.board_summary else (result.risks|length if result.risks else 0) }}
                                </div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-card-label">Start Score</div>
                                <div class="stat-card-value">
                                    {{ result.score_explanation.start_score if result.score_explanation else 10 }}
                                </div>
                            </div>
                        </div>

                        <div class="summary-card">
                            <div class="summary-title">{{ result.health_summary.title }}</div>
                            <p class="summary-copy">{{ result.health_summary.summary }}</p>
                        </div>

                        <div class="split-tight" style="margin-top: 16px;">
                            <div class="top-issue-card">
                                <div class="summary-title">Top Issues</div>
                                <p class="summary-copy">Most important findings to review first.</p>
                                {% if result.top_issues %}
                                    <div class="stack" style="margin-top: 12px;">
                                        {% for issue in result.top_issues %}
                                            <div class="top-issue-item">
                                                <span class="severity-pill {{ severity_class(issue.severity) }}">{{ issue.severity }}</span>
                                                <div class="finding-title" style="font-size: 16px;">{{ issue.message }}</div>
                                                <p class="finding-subtitle">{{ issue.category }}</p>
                                            </div>
                                        {% endfor %}
                                    </div>
                                {% else %}
                                    <p class="muted-note" style="margin-top: 12px;">No issues found.</p>
                                {% endif %}
                            </div>

                            <div class="top-issue-card">
                                <div class="summary-title">Category Summary</div>
                                <p class="summary-copy">Quick count by grouped section.</p>
                                {% if result.grouped_risks %}
                                    <div class="stack" style="margin-top: 12px;">
                                        {% for section in result.grouped_risks %}
                                            <div class="finding-box">
                                                <div class="finding-box-label">{{ section.title }}</div>
                                                <div class="finding-box-value">
                                                    {{ section.count }} issue{% if section.count != 1 %}s{% endif %}
                                                </div>
                                            </div>
                                        {% endfor %}
                                    </div>
                                {% else %}
                                    <p class="muted-note" style="margin-top: 12px;">No grouped findings.</p>
                                {% endif %}
                            </div>
                        </div>

                        {% if result.score_explanation %}
                            <h3 class="section-title">Score Breakdown</h3>
                            <div class="split">
                                <div class="form-card">
                                    <div class="form-card-title">Penalty Summary</div>
                                    <div class="form-card-copy">
                                        Clear view of how much score was removed.
                                    </div>
                                    <div class="grid-stats" style="grid-template-columns: repeat(2, minmax(0, 1fr)); margin-bottom: 0;">
                                        <div class="stat-card">
                                            <div class="stat-card-label">Start</div>
                                            <div class="stat-card-value">{{ result.score_explanation.start_score }}</div>
                                        </div>
                                        <div class="stat-card">
                                            <div class="stat-card-label">Total Penalty</div>
                                            <div class="stat-card-value">{{ result.score_explanation.total_penalty }}</div>
                                        </div>
                                    </div>
                                </div>

                                <div class="form-card">
                                    <div class="form-card-title">Penalty Distribution</div>
                                    <div class="form-card-copy">
                                        Severity and category totals that drove the score.
                                    </div>

                                    {% if result.score_explanation.severity_totals %}
                                        <div class="chip-row" style="margin-bottom: 10px;">
                                            {% for severity, penalty in result.score_explanation.severity_totals.items() %}
                                                <span class="chip {{ chip_class(severity) }}">{{ severity }}: {{ penalty }}</span>
                                            {% endfor %}
                                        </div>
                                    {% endif %}

                                    {% if result.score_explanation.category_totals %}
                                        <div class="chip-row">
                                            {% for category, penalty in result.score_explanation.category_totals.items() %}
                                                <span class="chip">{{ category }}: {{ penalty }}</span>
                                            {% endfor %}
                                        </div>
                                    {% else %}
                                        <p class="muted-note">No category penalties recorded.</p>
                                    {% endif %}
                                </div>
                            </div>
                        {% endif %}

                        <h3 class="section-title">Grouped Findings</h3>

                        {% if result.grouped_risks %}
                            <div class="finding-list">
                                {% for section in result.grouped_risks %}
                                    <div class="category-card">
                                        <div class="category-top">
                                            <div>
                                                <div class="category-title">{{ section.title }}</div>
                                                <p class="category-subtitle">
                                                    {{ section.count }} finding{% if section.count != 1 %}s{% endif %} in this category
                                                </p>
                                            </div>

                                            <div class="chip-row">
                                                {% if section.severity_counts.critical %}
                                                    <span class="chip chip-critical">critical: {{ section.severity_counts.critical }}</span>
                                                {% endif %}
                                                {% if section.severity_counts.high %}
                                                    <span class="chip chip-high">high: {{ section.severity_counts.high }}</span>
                                                {% endif %}
                                                {% if section.severity_counts.medium %}
                                                    <span class="chip chip-medium">medium: {{ section.severity_counts.medium }}</span>
                                                {% endif %}
                                                {% if section.severity_counts.low %}
                                                    <span class="chip chip-low">low: {{ section.severity_counts.low }}</span>
                                                {% endif %}
                                            </div>
                                        </div>

                                        <div class="finding-list" style="margin-top: 14px;">
                                            {% for risk in section.risks %}
                                                <div class="finding-card">
                                                    <div class="finding-top">
                                                        <div>
                                                            <span class="severity-pill {{ severity_class(risk.severity) }}">
                                                                {{ risk.severity }}
                                                            </span>
                                                            <div class="finding-title">{{ risk.message }}</div>
                                                            <p class="finding-subtitle">
                                                                {% if risk.rule_id %}Rule: {{ risk.rule_id }}{% else %}Grouped finding{% endif %}
                                                            </p>
                                                        </div>
                                                    </div>

                                                    <div class="finding-body">
                                                        <div class="finding-box">
                                                            <div class="finding-box-label">Recommendation</div>
                                                            <div class="finding-box-value">
                                                                {{ risk.recommendation if risk.recommendation else "Manual review recommended." }}
                                                            </div>
                                                        </div>

                                                        {% if risk.explanation %}
                                                            <div class="finding-box">
                                                                <div class="finding-box-label">Explanation</div>
                                                                <div class="finding-box-value">
                                                                    {% if risk.explanation.root_cause %}<strong>Root cause:</strong> {{ risk.explanation.root_cause }}<br />{% endif %}
                                                                    {% if risk.explanation.impact %}<strong>Impact:</strong> {{ risk.explanation.impact }}<br />{% endif %}
                                                                    {% if risk.explanation.confidence %}<strong>Confidence:</strong> {{ risk.explanation.confidence }}{% endif %}
                                                                </div>
                                                            </div>
                                                        {% endif %}
                                                    </div>

                                                    <div class="meta-row">
                                                        {% if risk.components %}
                                                            <span class="meta-chip">Components: {{ risk.components | join(", ") }}</span>
                                                        {% endif %}
                                                        {% if risk.nets %}
                                                            <span class="meta-chip">Nets: {{ risk.nets | join(", ") }}</span>
                                                        {% endif %}
                                                        {% if risk.region %}
                                                            <span class="meta-chip">Region: {{ risk.region }}</span>
                                                        {% endif %}
                                                    </div>
                                                </div>
                                            {% endfor %}
                                        </div>
                                    </div>
                                {% endfor %}
                            </div>
                        {% else %}
                            <div class="finding-card">
                                <div class="finding-title">No risks detected</div>
                                <p class="finding-subtitle">
                                    This board did not produce any findings in the current ruleset and config state.
                                </p>
                            </div>
                        {% endif %}

                        {% if result.downloads %}
                            <h3 class="section-title">Exports</h3>
                            <div class="downloads">
                                {% for item in result.downloads %}
                                    <a class="download-link" href="{{ download_href(item) }}">{{ item.label }}</a>
                                {% endfor %}
                            </div>
                        {% endif %}
                    </section>
                {% endif %}

                {% if project_result %}
                    <section class="panel">
                        <div class="result-header">
                            <div>
                                <div class="result-eyebrow">Project Ranking Review</div>
                                <h2 class="result-title">Board Ranking and Health Comparison</h2>
                                <p class="result-copy">
                                    Compare boards across the uploaded project set and identify which designs deserve attention first.
                                </p>
                            </div>
                        </div>

                        {% if project_result.project_summary %}
                            <div class="grid-stats">
                                <div class="stat-card">
                                    <div class="stat-card-label">Boards</div>
                                    <div class="stat-card-value">{{ project_result.project_summary.total_boards }}</div>
                                </div>
                                <div class="stat-card">
                                    <div class="stat-card-label">Average Score</div>
                                    <div class="stat-card-value">{{ project_result.project_summary.average_score }}</div>
                                </div>
                                <div class="stat-card">
                                    <div class="stat-card-label">Best Score</div>
                                    <div class="stat-card-value">{{ project_result.project_summary.best_score }}</div>
                                </div>
                                <div class="stat-card">
                                    <div class="stat-card-label">Worst Score</div>
                                    <div class="stat-card-value">{{ project_result.project_summary.worst_score }}</div>
                                </div>
                            </div>
                        {% endif %}

                        <h3 class="section-title">Ranked Boards</h3>

                        {% if project_result.boards %}
                            <div class="board-list">
                                {% for board in project_result.boards %}
                                    <div class="board-card">
                                        <div class="board-top">
                                            <div style="display: flex; gap: 14px; align-items: flex-start;">
                                                <div class="board-rank">#{{ board.rank }}</div>
                                                <div>
                                                    <div class="rank-label">
                                                        {% if board.rank == 1 %}Top ranked board{% elif board.rank == project_result.boards|length %}Lowest ranked board{% else %}Project board{% endif %}
                                                    </div>
                                                    <div class="board-title">{{ board.filename }}</div>
                                                    <p class="board-subtitle">{{ board.health_summary.title }}</p>
                                                </div>
                                            </div>

                                            <div class="score-card" style="min-width: 170px;">
                                                <div class="score-label">Score</div>
                                                <div class="board-score">{{ board.score }}</div>
                                                <div class="score-band {{ score_band_class(board.score) }}">
                                                    {{ score_band_label(board.score) }}
                                                </div>
                                            </div>
                                        </div>

                                        <div class="finding-box" style="margin-top: 14px;">
                                            <div class="finding-box-label">Health Summary</div>
                                            <div class="finding-box-value">{{ board.health_summary.summary }}</div>
                                        </div>

                                        {% if board.top_issues %}
                                            <div class="finding-list" style="margin-top: 14px;">
                                                {% for risk in board.top_issues %}
                                                    <div class="finding-box">
                                                        <div class="finding-box-label">{{ risk.severity }} · {{ risk.category }}</div>
                                                        <div class="finding-box-value">
                                                            <strong>{{ risk.message }}</strong><br />
                                                            {{ risk.recommendation if risk.recommendation else "Manual review recommended." }}
                                                        </div>
                                                    </div>
                                                {% endfor %}
                                            </div>
                                        {% else %}
                                            <div class="finding-box" style="margin-top: 14px;">
                                                <div class="finding-box-label">Top Issues</div>
                                                <div class="finding-box-value">No issues detected.</div>
                                            </div>
                                        {% endif %}
                                    </div>
                                {% endfor %}
                            </div>
                        {% else %}
                            <p class="muted-note">No board ranking data available.</p>
                        {% endif %}

                        {% if project_result.downloads %}
                            <h3 class="section-title">Project Exports</h3>
                            <div class="downloads">
                                {% for item in project_result.downloads %}
                                    <a class="download-link" href="{{ download_href(item) }}">{{ item.label }}</a>
                                {% endfor %}
                            </div>
                        {% endif %}
                    </section>
                {% endif %}

                {% if not result and not project_result %}
                    <section class="panel">
                        <div class="result-eyebrow">Phase 2 Focus</div>
                        <h2 class="result-title">Review flow and product presentation</h2>
                        <p class="result-copy">
                            The engine is now stable. Phase 2 upgrades how findings are presented: top issues first,
                            grouped categories second, and better board-ranking review for projects.
                        </p>

                        <div class="grid-stats" style="margin-top: 18px;">
                            <div class="stat-card">
                                <div class="stat-card-label">Phase 2 Step 1</div>
                                <div class="stat-card-value" style="font-size: 20px;">Grouped Findings</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-card-label">Phase 2 Step 2</div>
                                <div class="stat-card-value" style="font-size: 20px;">Top Issues</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-card-label">Phase 2 Step 3</div>
                                <div class="stat-card-value" style="font-size: 20px;">Board Health</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-card-label">Phase 2 Step 4</div>
                                <div class="stat-card-value" style="font-size: 20px;">Better Reports</div>
                            </div>
                        </div>

                        <p class="footer-note">
                            Upload a board or a project set to review the new grouped Phase 2 experience.
                        </p>
                    </section>
                {% endif %}
            </div>
        </div>
    </div>
</body>
</html>
"""


def render_dashboard(config, result=None, project_result=None):
    return render_template_string(
        HTML_TEMPLATE,
        config=config,
        result=result,
        project_result=project_result,
        recent_runs=get_recent_runs(RUNS_FOLDER),
    )


@app.route("/", methods=["GET"])
def index():
    _, config_view = get_dashboard_config(CONFIG_PATH)
    return render_dashboard(config_view)


@app.route("/save_config", methods=["POST"])
def save_config_route():
    try:
        updated_config = parse_config_form(request.form, CONFIG_PATH)
        save_config(updated_config, CONFIG_PATH)
        flash("Config updated successfully.")
    except ValueError:
        flash("Config update failed. Please check your numeric values.")
    except OSError:
        flash("Config update failed. Could not write custom_config.json.")

    return redirect(url_for("index"))


@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        service_result = analyze_single_board(
            uploaded_file=request.files.get("single_file"),
            upload_folder=UPLOAD_FOLDER,
            runs_folder=RUNS_FOLDER,
            config_path=CONFIG_PATH,
        )

        result = _enrich_single_result(service_result["result"])

        return render_dashboard(
            config=service_result["config_view"],
            result=result,
        )
    except ValueError as error:
        flash(str(error))
        return redirect(url_for("index"))
    except Exception as error:
        flash(f"Analysis failed: {error}")
        return redirect(url_for("index"))


@app.route("/analyze_project", methods=["POST"])
def analyze_project():
    try:
        service_result = analyze_project_files(
            uploaded_files=request.files.getlist("project_files"),
            upload_folder=UPLOAD_FOLDER,
            runs_folder=RUNS_FOLDER,
            config_path=CONFIG_PATH,
        )

        project_result = _enrich_project_result(service_result["project_result"])

        return render_dashboard(
            config=service_result["config_view"],
            project_result=project_result,
        )
    except ValueError as error:
        flash(str(error))
        return redirect(url_for("index"))
    except Exception as error:
        flash(f"Project analysis failed: {error}")
        return redirect(url_for("index"))


@app.route("/download/<run_dir>/<filename>", methods=["GET"])
def download_file(run_dir, filename):
    return send_from_directory(
        os.path.join(RUNS_FOLDER, run_dir),
        filename,
        as_attachment=True,
    )


if __name__ == "__main__":
    app.run(debug=True)