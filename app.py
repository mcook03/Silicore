import json
import os
import shutil
from datetime import datetime

from flask import Flask, request, redirect, url_for, render_template_string, send_file
from werkzeug.utils import secure_filename

from engine.config import DEFAULT_CONFIG
from engine.config_loader import load_config
from engine.parser import parse_pcb_file
from engine.kicad_parser import parse_kicad_file
from engine.normalizer import normalize_pcb
from engine.rule_runner import run_analysis
from engine.report_generator import generate_report


app = Flask(__name__)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "dashboard_uploads")
RUNS_DIR = os.path.join(BASE_DIR, "dashboard_runs")
CUSTOM_CONFIG_PATH = os.path.join(BASE_DIR, "custom_config.json")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RUNS_DIR, exist_ok=True)


def get_active_config():
    if os.path.exists(CUSTOM_CONFIG_PATH):
        try:
            loaded = load_config(CUSTOM_CONFIG_PATH)
            if isinstance(loaded, dict):
                merged = dict(DEFAULT_CONFIG)
                merged.update(loaded)
                return merged
        except Exception:
            pass
    return dict(DEFAULT_CONFIG)


def timestamp_string():
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")


def parse_uploaded_board(file_path):
    extension = os.path.splitext(file_path)[1].lower()

    if extension == ".kicad_pcb":
        pcb = parse_kicad_file(file_path)
    else:
        pcb = parse_pcb_file(file_path)

    return normalize_pcb(pcb)


def save_json(data, output_path):
    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


def save_text(text, output_path):
    with open(output_path, "w", encoding="utf-8") as file:
        file.write(text)


def markdown_to_basic_html(markdown_text, title="Silicore Report"):
    escaped = (
        markdown_text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{title}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 32px;
            line-height: 1.6;
            background: #f8f9fb;
            color: #1f2937;
        }}
        .report {{
            background: white;
            padding: 24px;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
            max-width: 1100px;
            margin: 0 auto;
        }}
        pre {{
            white-space: pre-wrap;
            word-wrap: break-word;
            font-family: "Courier New", monospace;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="report">
        <pre>{escaped}</pre>
    </div>
</body>
</html>
"""


def build_score_explanation_html(score_explanation):
    if not score_explanation:
        return "<p>No score explanation available.</p>"

    severity_html = ""
    for severity, penalty in sorted(score_explanation.get("severity_totals", {}).items()):
        severity_html += f"<li><strong>{severity.title()}</strong>: {penalty}</li>"

    category_html = ""
    for category, penalty in sorted(score_explanation.get("category_totals", {}).items()):
        category_html += f"<li><strong>{category}</strong>: {penalty}</li>"

    detail_html = ""
    for item in score_explanation.get("detailed_penalties", []):
        components = ", ".join(item.get("components", [])) if item.get("components") else "None"
        nets = ", ".join(item.get("nets", [])) if item.get("nets") else "None"

        detail_html += (
            "<li style='margin-bottom:10px;'>"
            f"<strong>{item.get('rule_id', 'UNKNOWN_RULE')}</strong> | "
            f"{item.get('severity', 'low').title()} | "
            f"{item.get('category', 'uncategorized')} | "
            f"Penalty: {item.get('penalty', 0)}"
            f"<br>{item.get('message', 'No message')}"
            f"<br><strong>Components:</strong> {components}"
            f"<br><strong>Nets:</strong> {nets}"
            "</li>"
        )

    return f"""
    <div class="score-box">
        <div class="section-header">
            <h3>Score Explainability</h3>
            <span class="subtle-chip">Trust Layer</span>
        </div>

        <div class="stats-grid">
            <div class="mini-stat">
                <span class="mini-label">Start Score</span>
                <span class="mini-value">{score_explanation.get('start_score', 10.0)}</span>
            </div>
            <div class="mini-stat">
                <span class="mini-label">Total Penalty</span>
                <span class="mini-value">{score_explanation.get('total_penalty', 0.0)}</span>
            </div>
            <div class="mini-stat">
                <span class="mini-label">Final Score</span>
                <span class="mini-value">{score_explanation.get('final_score', 0.0)}</span>
            </div>
        </div>

        <div class="two-column-block">
            <div>
                <h4>Penalty by Severity</h4>
                <ul>{severity_html or "<li>None</li>"}</ul>
            </div>
            <div>
                <h4>Penalty by Category</h4>
                <ul>{category_html or "<li>None</li>"}</ul>
            </div>
        </div>

        <details style="margin-top: 14px;">
            <summary><strong>Detailed Penalties</strong></summary>
            <ul style="margin-top: 12px;">{detail_html or "<li>None</li>"}</ul>
        </details>
    </div>
    """


def build_risk_list_html(risks):
    if not risks:
        return "<p>No risks found.</p>"

    parts = []

    for risk in risks:
        severity = str(risk.get("severity", "low")).lower()
        category = risk.get("category", "uncategorized")
        components = ", ".join(risk.get("components", [])) if risk.get("components") else "None"
        nets = ", ".join(risk.get("nets", [])) if risk.get("nets") else "None"
        metrics = risk.get("metrics", {})

        parts.append(f"""
        <div class="risk-card severity-{severity}" data-severity="{severity}" data-category="{category}">
            <div class="risk-top-row">
                <div class="risk-main">
                    <h4>{severity.upper()} — {risk.get('message', 'No message')}</h4>
                    <p class="risk-meta"><strong>Rule ID:</strong> {risk.get('rule_id', 'UNKNOWN_RULE')}</p>
                </div>
                <div class="pill-group">
                    <span class="pill pill-severity">{severity.title()}</span>
                    <span class="pill pill-category">{category}</span>
                </div>
            </div>
            <div class="risk-detail-grid">
                <p><strong>Components:</strong> {components}</p>
                <p><strong>Nets:</strong> {nets}</p>
            </div>
            <p><strong>Metrics:</strong> {metrics}</p>
            <p><strong>Recommendation:</strong> {risk.get('recommendation', 'No recommendation provided')}</p>
        </div>
        """)

    return "\n".join(parts)


def create_single_run(board_name, analysis_result, markdown_report):
    run_id = f"single_{timestamp_string()}"
    run_dir = os.path.join(RUNS_DIR, run_id)
    os.makedirs(run_dir, exist_ok=True)

    json_path = os.path.join(run_dir, "single_analysis.json")
    md_path = os.path.join(run_dir, "single_report.md")
    html_path = os.path.join(run_dir, "single_report.html")
    meta_path = os.path.join(run_dir, "run_meta.json")

    save_json(analysis_result, json_path)
    save_text(markdown_report, md_path)
    save_text(markdown_to_basic_html(markdown_report, "Silicore Single Report"), html_path)

    run_meta = {
        "run_id": run_id,
        "run_type": "single",
        "created_at": datetime.now().isoformat(),
        "board_name": board_name,
        "score": analysis_result.get("score", 0),
        "files": {
            "json": "single_analysis.json",
            "markdown": "single_report.md",
            "html": "single_report.html",
        },
    }
    save_json(run_meta, meta_path)

    return run_id, run_dir


def create_project_run(project_results):
    run_id = f"project_{timestamp_string()}"
    run_dir = os.path.join(RUNS_DIR, run_id)
    os.makedirs(run_dir, exist_ok=True)

    summary = {
        "run_id": run_id,
        "run_type": "project",
        "created_at": datetime.now().isoformat(),
        "board_count": len(project_results),
        "boards": project_results,
        "best_board": project_results[0]["board_name"] if project_results else None,
        "worst_board": project_results[-1]["board_name"] if project_results else None,
    }

    md_lines = [
        "# SILICORE PROJECT SUMMARY",
        "",
        f"- Board Count: {len(project_results)}",
        "",
    ]

    for board in project_results:
        md_lines.extend([
            f"## Rank {board['rank']} — {board['board_name']}",
            f"- Score: {board['score']} / 10",
            f"- Total Risks: {board['risk_summary'].get('total_risks', 0)}",
            "",
        ])

    markdown_report = "\n".join(md_lines)

    json_path = os.path.join(run_dir, "project_summary.json")
    md_path = os.path.join(run_dir, "project_summary.md")
    html_path = os.path.join(run_dir, "project_summary.html")
    meta_path = os.path.join(run_dir, "run_meta.json")

    save_json(summary, json_path)
    save_text(markdown_report, md_path)
    save_text(markdown_to_basic_html(markdown_report, "Silicore Project Summary"), html_path)

    run_meta = {
        "run_id": run_id,
        "run_type": "project",
        "created_at": datetime.now().isoformat(),
        "board_count": len(project_results),
        "best_board": project_results[0]["board_name"] if project_results else None,
        "worst_board": project_results[-1]["board_name"] if project_results else None,
        "files": {
            "json": "project_summary.json",
            "markdown": "project_summary.md",
            "html": "project_summary.html",
        },
    }
    save_json(run_meta, meta_path)

    return run_id, run_dir


def load_recent_runs(limit=10):
    runs = []

    if not os.path.exists(RUNS_DIR):
        return runs

    for entry in os.listdir(RUNS_DIR):
        run_dir = os.path.join(RUNS_DIR, entry)
        meta_path = os.path.join(run_dir, "run_meta.json")

        if os.path.isdir(run_dir) and os.path.exists(meta_path):
            try:
                with open(meta_path, "r", encoding="utf-8") as file:
                    meta = json.load(file)
                    runs.append(meta)
            except Exception:
                continue

    runs.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    return runs[:limit]


def render_home():
    recent_runs = load_recent_runs()

    return render_template_string(
        """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Silicore Dashboard</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            background: linear-gradient(180deg, #edf2f8 0%, #f7f9fc 100%);
            color: #111827;
        }
        .container {
            max-width: 1240px;
            margin: 0 auto;
            padding: 32px;
        }
        .hero {
            background: linear-gradient(135deg, #0f172a, #1e293b 55%, #334155);
            color: white;
            padding: 34px;
            border-radius: 22px;
            margin-bottom: 24px;
            box-shadow: 0 18px 40px rgba(15, 23, 42, 0.22);
            border: 1px solid rgba(255,255,255,0.06);
        }
        .hero h1 {
            margin-top: 0;
            margin-bottom: 10px;
            font-size: 36px;
            letter-spacing: -0.02em;
        }
        .hero p {
            margin: 0;
            color: #cbd5e1;
            max-width: 760px;
        }
        .hero-top {
            display: flex;
            justify-content: space-between;
            gap: 18px;
            align-items: flex-start;
        }
        .build-note {
            font-size: 12px;
            color: #cbd5e1;
            background: rgba(255,255,255,0.08);
            padding: 8px 12px;
            border-radius: 999px;
            white-space: nowrap;
        }
        .home-stats {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
            margin-top: 20px;
        }
        .home-stat {
            background: rgba(255,255,255,0.08);
            border: 1px solid rgba(255,255,255,0.08);
            padding: 16px;
            border-radius: 14px;
            backdrop-filter: blur(4px);
        }
        .home-stat .label {
            display: block;
            color: #cbd5e1;
            font-size: 12px;
            margin-bottom: 6px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .home-stat .value {
            font-size: 24px;
            font-weight: 700;
        }
        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
        }
        .card {
            background: rgba(255,255,255,0.88);
            backdrop-filter: blur(8px);
            padding: 24px;
            border-radius: 20px;
            box-shadow: 0 12px 28px rgba(15, 23, 42, 0.08);
            border: 1px solid rgba(255,255,255,0.5);
        }
        .card h2 {
            margin-top: 0;
            margin-bottom: 10px;
        }
        .recent-run {
            padding: 16px;
            border: 1px solid #e5e7eb;
            border-radius: 14px;
            margin-bottom: 12px;
            background: #fafafa;
        }
        input[type=file] {
            margin: 12px 0;
            width: 100%;
            padding: 10px;
            border: 1px dashed #cbd5e1;
            border-radius: 12px;
            background: #f8fafc;
        }
        button {
            background: linear-gradient(135deg, #111827, #1f2937);
            color: white;
            border: none;
            padding: 12px 18px;
            border-radius: 12px;
            cursor: pointer;
            font-weight: 600;
            box-shadow: 0 10px 20px rgba(17, 24, 39, 0.16);
        }
        button:hover {
            opacity: 0.95;
        }
        a {
            color: #2563eb;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        .note {
            color: #6b7280;
            font-size: 14px;
        }
        .footer-note {
            margin-top: 20px;
            text-align: center;
            font-size: 12px;
            color: #6b7280;
        }
        @media (max-width: 900px) {
            .grid, .home-stats {
                grid-template-columns: 1fr;
            }
            .hero-top {
                flex-direction: column;
            }
            .build-note {
                white-space: normal;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="hero">
            <div class="hero-top">
                <div>
                    <h1>Silicore Dashboard</h1>
                    <p>PCB risk analysis, project ranking, explainable scoring, and downloadable reports.</p>
                </div>
                <div class="build-note">Dev Build - Milestone 11</div>
            </div>

            <div class="home-stats">
                <div class="home-stat">
                    <span class="label">Saved Runs</span>
                    <span class="value">{{ recent_runs|length }}</span>
                </div>
                <div class="home-stat">
                    <span class="label">Ranking Model</span>
                    <span class="value">1 = Best</span>
                </div>
                <div class="home-stat">
                    <span class="label">Supported Inputs</span>
                    <span class="value">.txt, .kicad_pcb</span>
                </div>
            </div>
        </div>

        <div class="grid">
            <div class="card">
                <h2>Single Board Analysis</h2>
                <form action="/analyze" method="post" enctype="multipart/form-data">
                    <input type="file" name="board_file" required>
                    <button type="submit">Analyze Board</button>
                </form>
                <p class="note">Upload one board file for individual analysis and explainable scoring.</p>
            </div>

            <div class="card">
                <h2>Project Analysis</h2>
                <form action="/project" method="post" enctype="multipart/form-data">
                    <input type="file" name="board_files" multiple required>
                    <button type="submit">Analyze Project</button>
                </form>
                <p class="note">Select all files at once. Rank 1 is best. Higher number is worse.</p>
            </div>
        </div>

        <div class="card" style="margin-top: 24px;">
            <h2>Recent Saved Runs</h2>
            {% if recent_runs %}
                {% for run in recent_runs %}
                    <div class="recent-run">
                        <p><strong>{{ run.run_type.title() }} Run</strong></p>
                        <p><strong>Created:</strong> {{ run.created_at }}</p>

                        {% if run.run_type == 'single' %}
                            <p><strong>Board:</strong> {{ run.board_name }}</p>
                            <p><strong>Score:</strong> {{ run.score }}</p>
                        {% else %}
                            <p><strong>Board Count:</strong> {{ run.board_count }}</p>
                            <p><strong>Best Board:</strong> {{ run.best_board }}</p>
                            <p><strong>Worst Board:</strong> {{ run.worst_board }}</p>
                        {% endif %}

                        <p>
                            <a href="/download/{{ run.run_id }}/json">JSON</a> |
                            <a href="/download/{{ run.run_id }}/markdown">Markdown</a> |
                            <a href="/download/{{ run.run_id }}/html">HTML</a>
                        </p>
                    </div>
                {% endfor %}
            {% else %}
                <p>No saved runs yet.</p>
            {% endif %}
        </div>

        <div class="footer-note">Dev Build - Milestone 11</div>
    </div>
</body>
</html>
        """,
        recent_runs=recent_runs,
    )


@app.route("/", methods=["GET"])
def home():
    return render_home()


@app.route("/analyze", methods=["POST"])
def analyze_board():
    uploaded_file = request.files.get("board_file")

    if not uploaded_file or uploaded_file.filename.strip() == "":
        return redirect(url_for("home"))

    config = get_active_config()

    temp_dir = os.path.join(UPLOAD_DIR, f"single_{timestamp_string()}")
    os.makedirs(temp_dir, exist_ok=True)

    filename = secure_filename(uploaded_file.filename)
    file_path = os.path.join(temp_dir, filename)
    uploaded_file.save(file_path)

    try:
        pcb = parse_uploaded_board(file_path)
        analysis_result = run_analysis(pcb, config, debug=False)
        markdown_report = generate_report(pcb, analysis_result)
        run_id, _ = create_single_run(filename, analysis_result, markdown_report)
    except Exception as exc:
        shutil.rmtree(temp_dir, ignore_errors=True)
        return f"<h2>Analysis failed</h2><p>{exc}</p>", 500

    shutil.rmtree(temp_dir, ignore_errors=True)

    score_explanation_html = build_score_explanation_html(
        analysis_result.get("score_explanation", {})
    )
    risk_list_html = build_risk_list_html(analysis_result.get("risks", []))
    risk_summary = analysis_result.get("risk_summary", {})
    by_severity = risk_summary.get("by_severity", {})
    by_category = risk_summary.get("by_category", {})

    severity_options = sorted(
        {str(risk.get("severity", "low")).lower() for risk in analysis_result.get("risks", [])}
    )
    category_options = sorted(
        {str(risk.get("category", "uncategorized")) for risk in analysis_result.get("risks", [])}
    )

    return render_template_string(
        """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Silicore Single Board Result</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            background: linear-gradient(180deg, #edf2f8 0%, #f7f9fc 100%);
            color: #111827;
        }
        .container {
            max-width: 1180px;
            margin: 0 auto;
            padding: 32px;
        }
        .card, .score-box, .risk-card, .summary-card, .filter-card {
            background: rgba(255,255,255,0.9);
            backdrop-filter: blur(8px);
            padding: 22px;
            border-radius: 18px;
            box-shadow: 0 12px 28px rgba(15, 23, 42, 0.08);
            margin-bottom: 20px;
            border: 1px solid rgba(255,255,255,0.5);
        }
        .severity-low { border-left: 6px solid #10b981; }
        .severity-medium { border-left: 6px solid #f59e0b; }
        .severity-high { border-left: 6px solid #f97316; }
        .severity-critical { border-left: 6px solid #ef4444; }
        a {
            color: #2563eb;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        .top-links {
            margin-bottom: 20px;
        }
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 18px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
        }
        .mini-stat, .summary-card {
            background: #f8fafc;
            border: 1px solid #e5e7eb;
            border-radius: 14px;
            padding: 14px;
        }
        .mini-label {
            display: block;
            font-size: 12px;
            color: #6b7280;
            margin-bottom: 6px;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }
        .mini-value {
            font-size: 20px;
            font-weight: 700;
        }
        .risk-top-row {
            display: flex;
            justify-content: space-between;
            gap: 16px;
            align-items: flex-start;
        }
        .risk-main h4 {
            margin-top: 0;
            margin-bottom: 6px;
        }
        .pill-group {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }
        .pill {
            display: inline-block;
            padding: 6px 10px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 700;
        }
        .pill-severity {
            background: #dbeafe;
            color: #1d4ed8;
        }
        .pill-category {
            background: #ede9fe;
            color: #6d28d9;
        }
        .risk-meta {
            color: #6b7280;
            margin-top: 6px;
        }
        .filter-row {
            display: grid;
            grid-template-columns: 1fr 1fr auto;
            gap: 12px;
            align-items: end;
        }
        .risk-detail-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
        }
        .section-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            margin-bottom: 14px;
        }
        .subtle-chip {
            font-size: 12px;
            padding: 6px 10px;
            border-radius: 999px;
            background: #eff6ff;
            color: #1d4ed8;
            font-weight: 700;
        }
        .two-column-block {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 18px;
        }
        select, button.filter-btn {
            padding: 10px 12px;
            border-radius: 12px;
            border: 1px solid #d1d5db;
            font-size: 14px;
            background: white;
        }
        button.filter-btn {
            background: linear-gradient(135deg, #111827, #1f2937);
            color: white;
            border: none;
            cursor: pointer;
            font-weight: 600;
        }
        .empty-note {
            color: #6b7280;
            font-style: italic;
            padding: 8px 0;
        }
        .page-title-card {
            background: linear-gradient(135deg, #ffffff, #f8fafc);
        }
        @media (max-width: 900px) {
            .summary-grid, .stats-grid, .filter-row, .two-column-block, .risk-detail-grid {
                grid-template-columns: 1fr;
            }
            .risk-top-row {
                flex-direction: column;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="top-links">
            <a href="/">← Back to Dashboard</a>
        </div>

        <div class="card page-title-card">
            <div class="section-header">
                <div>
                    <h1 style="margin: 0;">Single Board Result</h1>
                    <p style="margin-top: 8px; color: #6b7280;"><strong>Board:</strong> {{ board_name }}</p>
                </div>
                <span class="subtle-chip">1 = Best Ranking Model</span>
            </div>
            <p><strong>Overall Risk Score:</strong> {{ score }} / 10</p>
            <p>
                <a href="/download/{{ run_id }}/json">Download JSON</a> |
                <a href="/download/{{ run_id }}/markdown">Download Markdown</a> |
                <a href="/download/{{ run_id }}/html">Download HTML</a>
            </p>
        </div>

        <div class="summary-grid">
            <div class="summary-card">
                <span class="mini-label">Total Risks</span>
                <span class="mini-value">{{ total_risks }}</span>
            </div>
            <div class="summary-card">
                <span class="mini-label">Low</span>
                <span class="mini-value">{{ by_severity.get('low', 0) }}</span>
            </div>
            <div class="summary-card">
                <span class="mini-label">Medium</span>
                <span class="mini-value">{{ by_severity.get('medium', 0) }}</span>
            </div>
            <div class="summary-card">
                <span class="mini-label">High + Critical</span>
                <span class="mini-value">{{ by_severity.get('high', 0) + by_severity.get('critical', 0) }}</span>
            </div>
        </div>

        <div class="summary-card">
            <div class="section-header">
                <h3 style="margin: 0;">Category Summary</h3>
                <span class="subtle-chip">Board Overview</span>
            </div>
            {% if by_category %}
                <div class="pill-group">
                    {% for category, count in by_category.items() %}
                        <span class="pill pill-category">{{ category }}: {{ count }}</span>
                    {% endfor %}
                </div>
            {% else %}
                <p>No category risks found.</p>
            {% endif %}
        </div>

        {{ score_explanation_html|safe }}

        <div class="filter-card">
            <div class="section-header">
                <h3 style="margin: 0;">Filter Findings</h3>
                <span class="subtle-chip">Interactive View</span>
            </div>
            <div class="filter-row">
                <div>
                    <label for="severityFilter"><strong>Severity</strong></label><br>
                    <select id="severityFilter">
                        <option value="all">All severities</option>
                        {% for value in severity_options %}
                            <option value="{{ value }}">{{ value.title() }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div>
                    <label for="categoryFilter"><strong>Category</strong></label><br>
                    <select id="categoryFilter">
                        <option value="all">All categories</option>
                        {% for value in category_options %}
                            <option value="{{ value }}">{{ value }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div>
                    <button class="filter-btn" type="button" onclick="resetFilters()">Reset Filters</button>
                </div>
            </div>
        </div>

        <div class="card">
            <div class="section-header">
                <h2 style="margin: 0;">Detailed Findings</h2>
                <span class="subtle-chip">Engineering Detail</span>
            </div>
            <div id="riskContainer">
                {{ risk_list_html|safe }}
            </div>
            <p id="emptyState" class="empty-note" style="display:none;">No findings match the selected filters.</p>
        </div>
    </div>

    <script>
        function applyFilters() {
            const severity = document.getElementById("severityFilter").value;
            const category = document.getElementById("categoryFilter").value;
            const cards = document.querySelectorAll(".risk-card");
            let visibleCount = 0;

            cards.forEach((card) => {
                const cardSeverity = card.getAttribute("data-severity");
                const cardCategory = card.getAttribute("data-category");

                const severityMatch = severity === "all" || cardSeverity === severity;
                const categoryMatch = category === "all" || cardCategory === category;

                if (severityMatch && categoryMatch) {
                    card.style.display = "block";
                    visibleCount += 1;
                } else {
                    card.style.display = "none";
                }
            });

            document.getElementById("emptyState").style.display = visibleCount === 0 ? "block" : "none";
        }

        function resetFilters() {
            document.getElementById("severityFilter").value = "all";
            document.getElementById("categoryFilter").value = "all";
            applyFilters();
        }

        document.getElementById("severityFilter").addEventListener("change", applyFilters);
        document.getElementById("categoryFilter").addEventListener("change", applyFilters);
    </script>
</body>
</html>
        """,
        board_name=filename,
        score=analysis_result.get("score", 0),
        total_risks=risk_summary.get("total_risks", 0),
        by_severity=by_severity,
        by_category=by_category,
        score_explanation_html=score_explanation_html,
        risk_list_html=risk_list_html,
        run_id=run_id,
        severity_options=severity_options,
        category_options=category_options,
    )


@app.route("/project", methods=["POST"])
def analyze_project():
    uploaded_files = request.files.getlist("board_files")

    if not uploaded_files:
        return redirect(url_for("home"))

    valid_files = [file for file in uploaded_files if file and file.filename.strip()]
    if not valid_files:
        return redirect(url_for("home"))

    config = get_active_config()

    temp_dir = os.path.join(UPLOAD_DIR, f"project_{timestamp_string()}")
    os.makedirs(temp_dir, exist_ok=True)

    board_results = []

    try:
        for uploaded_file in valid_files:
            filename = secure_filename(uploaded_file.filename)
            file_path = os.path.join(temp_dir, filename)
            uploaded_file.save(file_path)

            pcb = parse_uploaded_board(file_path)
            analysis_result = run_analysis(pcb, config, debug=False)

            board_results.append({
                "board_name": filename,
                "score": analysis_result.get("score", 0),
                "risks": analysis_result.get("risks", []),
                "risk_summary": analysis_result.get("risk_summary", {}),
                "score_explanation": analysis_result.get("score_explanation", {}),
            })

        board_results.sort(key=lambda item: item["score"], reverse=True)

        for index, board in enumerate(board_results, start=1):
            board["rank"] = index
            board["badge"] = "Best Board" if index == 1 else ("Worst Board" if index == len(board_results) else "")

        run_id, _ = create_project_run(board_results)

    except Exception as exc:
        shutil.rmtree(temp_dir, ignore_errors=True)
        return f"<h2>Project analysis failed</h2><p>{exc}</p>", 500

    shutil.rmtree(temp_dir, ignore_errors=True)

    all_categories = sorted({
        str(risk.get("category", "uncategorized"))
        for board in board_results
        for risk in board.get("risks", [])
    })

    all_severities = sorted({
        str(risk.get("severity", "low")).lower()
        for board in board_results
        for risk in board.get("risks", [])
    })

    return render_template_string(
        """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Silicore Project Results</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            background: linear-gradient(180deg, #edf2f8 0%, #f7f9fc 100%);
            color: #111827;
        }
        .container {
            max-width: 1240px;
            margin: 0 auto;
            padding: 32px;
        }
        .board-card, .summary-card, .score-box, .risk-card, .filter-card, .hero-card {
            background: rgba(255,255,255,0.9);
            backdrop-filter: blur(8px);
            padding: 22px;
            border-radius: 18px;
            box-shadow: 0 12px 28px rgba(15, 23, 42, 0.08);
            margin-bottom: 20px;
            border: 1px solid rgba(255,255,255,0.5);
        }
        .hero-card {
            background: linear-gradient(135deg, #ffffff, #f8fafc);
        }
        .badge {
            display: inline-block;
            color: white;
            padding: 6px 10px;
            border-radius: 999px;
            font-size: 12px;
            margin-left: 8px;
            font-weight: 700;
        }
        .badge-best {
            background: #059669;
        }
        .badge-worst {
            background: #dc2626;
        }
        .top-links {
            margin-bottom: 20px;
        }
        .severity-low { border-left: 6px solid #10b981; }
        .severity-medium { border-left: 6px solid #f59e0b; }
        .severity-high { border-left: 6px solid #f97316; }
        .severity-critical { border-left: 6px solid #ef4444; }
        a {
            color: #2563eb;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        .rank {
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 8px;
        }
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 18px;
            margin-bottom: 24px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
        }
        .mini-stat, .summary-card {
            background: #f8fafc;
            border: 1px solid #e5e7eb;
            border-radius: 14px;
            padding: 14px;
        }
        .mini-label {
            display: block;
            font-size: 12px;
            color: #6b7280;
            margin-bottom: 6px;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }
        .mini-value {
            font-size: 20px;
            font-weight: 700;
        }
        .pill-group {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }
        .pill {
            display: inline-block;
            padding: 6px 10px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 700;
        }
        .pill-severity {
            background: #dbeafe;
            color: #1d4ed8;
        }
        .pill-category {
            background: #ede9fe;
            color: #6d28d9;
        }
        .risk-top-row {
            display: flex;
            justify-content: space-between;
            gap: 16px;
            align-items: flex-start;
        }
        .risk-main h4 {
            margin-top: 0;
            margin-bottom: 6px;
        }
        .risk-meta {
            color: #6b7280;
            margin-top: 6px;
        }
        .board-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 16px;
            margin-bottom: 18px;
        }
        .filter-row {
            display: grid;
            grid-template-columns: 1fr 1fr auto;
            gap: 12px;
            align-items: end;
        }
        .risk-detail-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
        }
        .section-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            margin-bottom: 14px;
        }
        .subtle-chip {
            font-size: 12px;
            padding: 6px 10px;
            border-radius: 999px;
            background: #eff6ff;
            color: #1d4ed8;
            font-weight: 700;
        }
        .two-column-block {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 18px;
        }
        select, button.filter-btn {
            padding: 10px 12px;
            border-radius: 12px;
            border: 1px solid #d1d5db;
            font-size: 14px;
            background: white;
        }
        button.filter-btn {
            background: linear-gradient(135deg, #111827, #1f2937);
            color: white;
            border: none;
            cursor: pointer;
            font-weight: 600;
        }
        .empty-note {
            color: #6b7280;
            font-style: italic;
            padding: 8px 0;
        }
        @media (max-width: 900px) {
            .summary-grid, .stats-grid, .filter-row, .two-column-block, .risk-detail-grid {
                grid-template-columns: 1fr;
            }
            .board-header, .risk-top-row {
                flex-direction: column;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="top-links">
            <a href="/">← Back to Dashboard</a>
        </div>

        <div class="hero-card">
            <div class="section-header">
                <div>
                    <h1 style="margin: 0;">Project Results</h1>
                    <p style="margin-top: 8px; color: #6b7280;">
                        <strong>Board Count:</strong> {{ board_count }}
                    </p>
                </div>
                <span class="subtle-chip">Ranking: 1 = Best</span>
            </div>
            <p>
                <a href="/download/{{ run_id }}/json">Download JSON</a> |
                <a href="/download/{{ run_id }}/markdown">Download Markdown</a> |
                <a href="/download/{{ run_id }}/html">Download HTML</a>
            </p>
        </div>

        <div class="summary-grid">
            <div class="summary-card">
                <span class="mini-label">Best Board</span>
                <span class="mini-value">{{ board_results[0].board_name if board_results else "N/A" }}</span>
            </div>
            <div class="summary-card">
                <span class="mini-label">Worst Board</span>
                <span class="mini-value">{{ board_results[-1].board_name if board_results else "N/A" }}</span>
            </div>
            <div class="summary-card">
                <span class="mini-label">Highest Score</span>
                <span class="mini-value">{{ board_results[0].score if board_results else "N/A" }}</span>
            </div>
            <div class="summary-card">
                <span class="mini-label">Lowest Score</span>
                <span class="mini-value">{{ board_results[-1].score if board_results else "N/A" }}</span>
            </div>
        </div>

        <div class="filter-card">
            <div class="section-header">
                <h3 style="margin: 0;">Filter Project Findings</h3>
                <span class="subtle-chip">Interactive View</span>
            </div>
            <div class="filter-row">
                <div>
                    <label for="severityFilter"><strong>Severity</strong></label><br>
                    <select id="severityFilter">
                        <option value="all">All severities</option>
                        {% for value in all_severities %}
                            <option value="{{ value }}">{{ value.title() }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div>
                    <label for="categoryFilter"><strong>Category</strong></label><br>
                    <select id="categoryFilter">
                        <option value="all">All categories</option>
                        {% for value in all_categories %}
                            <option value="{{ value }}">{{ value }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div>
                    <button class="filter-btn" type="button" onclick="resetFilters()">Reset Filters</button>
                </div>
            </div>
        </div>

        {% for board in board_results %}
            <div class="board-card">
                <div class="board-header">
                    <div>
                        <div class="rank">
                            Rank {{ board.rank }} — {{ board.board_name }}
                            {% if board.badge == "Best Board" %}
                                <span class="badge badge-best">{{ board.badge }}</span>
                            {% elif board.badge == "Worst Board" %}
                                <span class="badge badge-worst">{{ board.badge }}</span>
                            {% endif %}
                        </div>
                    </div>
                    <span class="subtle-chip">Score {{ board.score }}</span>
                </div>

                <div class="summary-grid">
                    <div class="summary-card">
                        <span class="mini-label">Board Score</span>
                        <span class="mini-value">{{ board.score }}</span>
                    </div>
                    <div class="summary-card">
                        <span class="mini-label">Total Risks</span>
                        <span class="mini-value">{{ board.risk_summary.get('total_risks', 0) }}</span>
                    </div>
                    <div class="summary-card">
                        <span class="mini-label">High + Critical</span>
                        <span class="mini-value">
                            {{ board.risk_summary.get('by_severity', {}).get('high', 0) + board.risk_summary.get('by_severity', {}).get('critical', 0) }}
                        </span>
                    </div>
                    <div class="summary-card">
                        <span class="mini-label">Categories</span>
                        <span class="mini-value">{{ board.risk_summary.get('by_category', {})|length }}</span>
                    </div>
                </div>

                <div class="summary-card">
                    <div class="section-header">
                        <h3 style="margin: 0;">Category Summary</h3>
                        <span class="subtle-chip">Board Overview</span>
                    </div>
                    {% if board.risk_summary.get('by_category', {}) %}
                        <div class="pill-group">
                            {% for category, count in board.risk_summary.get('by_category', {}).items() %}
                                <span class="pill pill-category">{{ category }}: {{ count }}</span>
                            {% endfor %}
                        </div>
                    {% else %}
                        <p>No category risks found.</p>
                    {% endif %}
                </div>

                {{ build_score_explanation_html(board.score_explanation)|safe }}

                <div class="summary-card">
                    <div class="section-header">
                        <h3 style="margin: 0;">Detailed Findings</h3>
                        <span class="subtle-chip">Engineering Detail</span>
                    </div>
                    <div class="board-risks">
                        {% if board.risks %}
                            {% for risk in board.risks %}
                                <div class="risk-card severity-{{ risk.get('severity', 'low')|lower }}"
                                     data-severity="{{ risk.get('severity', 'low')|lower }}"
                                     data-category="{{ risk.get('category', 'uncategorized') }}">
                                    <div class="risk-top-row">
                                        <div class="risk-main">
                                            <h4>{{ risk.get('severity', 'low')|upper }} — {{ risk.get('message', 'No message') }}</h4>
                                            <p class="risk-meta"><strong>Rule ID:</strong> {{ risk.get('rule_id', 'UNKNOWN_RULE') }}</p>
                                        </div>
                                        <div class="pill-group">
                                            <span class="pill pill-severity">{{ risk.get('severity', 'low')|title }}</span>
                                            <span class="pill pill-category">{{ risk.get('category', 'uncategorized') }}</span>
                                        </div>
                                    </div>
                                    <div class="risk-detail-grid">
                                        <p><strong>Components:</strong> {{ ", ".join(risk.get('components', [])) if risk.get('components') else "None" }}</p>
                                        <p><strong>Nets:</strong> {{ ", ".join(risk.get('nets', [])) if risk.get('nets') else "None" }}</p>
                                    </div>
                                    <p><strong>Metrics:</strong> {{ risk.get('metrics', {}) }}</p>
                                    <p><strong>Recommendation:</strong> {{ risk.get('recommendation', 'No recommendation provided') }}</p>
                                </div>
                            {% endfor %}
                        {% else %}
                            <p>No risks found.</p>
                        {% endif %}
                    </div>
                </div>
            </div>
        {% endfor %}

        <p id="emptyState" class="empty-note" style="display:none;">No findings match the selected filters.</p>
    </div>

    <script>
        function applyFilters() {
            const severity = document.getElementById("severityFilter").value;
            const category = document.getElementById("categoryFilter").value;
            const cards = document.querySelectorAll(".risk-card");
            let visibleCount = 0;

            cards.forEach((card) => {
                const cardSeverity = card.getAttribute("data-severity");
                const cardCategory = card.getAttribute("data-category");

                const severityMatch = severity === "all" || cardSeverity === severity;
                const categoryMatch = category === "all" || cardCategory === category;

                if (severityMatch && categoryMatch) {
                    card.style.display = "block";
                    visibleCount += 1;
                } else {
                    card.style.display = "none";
                }
            });

            document.getElementById("emptyState").style.display = visibleCount === 0 ? "block" : "none";
        }

        function resetFilters() {
            document.getElementById("severityFilter").value = "all";
            document.getElementById("categoryFilter").value = "all";
            applyFilters();
        }

        document.getElementById("severityFilter").addEventListener("change", applyFilters);
        document.getElementById("categoryFilter").addEventListener("change", applyFilters);
    </script>
</body>
</html>
        """,
        board_results=board_results,
        board_count=len(board_results),
        run_id=run_id,
        build_score_explanation_html=build_score_explanation_html,
        all_categories=all_categories,
        all_severities=all_severities,
    )


@app.route("/download/<run_id>/<file_type>", methods=["GET"])
def download_run_file(run_id, file_type):
    run_dir = os.path.join(RUNS_DIR, run_id)
    meta_path = os.path.join(run_dir, "run_meta.json")

    if not os.path.exists(meta_path):
        return "<h2>Run not found</h2>", 404

    with open(meta_path, "r", encoding="utf-8") as file:
        meta = json.load(file)

    file_map = meta.get("files", {})
    filename = file_map.get(file_type)

    if not filename:
        return "<h2>Requested file type not found</h2>", 404

    target_path = os.path.join(run_dir, filename)

    if not os.path.exists(target_path):
        return "<h2>File missing</h2>", 404

    return send_file(target_path, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)