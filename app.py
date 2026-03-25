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


def ensure_clean_directory(path):
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path, exist_ok=True)


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
    for severity, penalty in score_explanation.get("severity_totals", {}).items():
        severity_html += f"<li><strong>{severity.title()}</strong>: {penalty}</li>"

    category_html = ""
    for category, penalty in score_explanation.get("category_totals", {}).items():
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
        <h3>Score Explainability</h3>
        <p><strong>Start Score:</strong> {score_explanation.get('start_score', 10.0)}</p>
        <p><strong>Total Penalty:</strong> {score_explanation.get('total_penalty', 0.0)}</p>
        <p><strong>Final Score:</strong> {score_explanation.get('final_score', 0.0)}</p>

        <h4>Penalty by Severity</h4>
        <ul>{severity_html or "<li>None</li>"}</ul>

        <h4>Penalty by Category</h4>
        <ul>{category_html or "<li>None</li>"}</ul>

        <h4>Detailed Penalties</h4>
        <ul>{detail_html or "<li>None</li>"}</ul>
    </div>
    """


def build_risk_list_html(risks):
    if not risks:
        return "<p>No risks found.</p>"

    parts = []
    for risk in risks:
        components = ", ".join(risk.get("components", [])) if risk.get("components") else "None"
        nets = ", ".join(risk.get("nets", [])) if risk.get("nets") else "None"
        metrics = risk.get("metrics", {})

        parts.append(f"""
        <div class="risk-card severity-{str(risk.get('severity', 'low')).lower()}">
            <h4>{str(risk.get('severity', 'low')).upper()} — {risk.get('message', 'No message')}</h4>
            <p><strong>Rule ID:</strong> {risk.get('rule_id', 'UNKNOWN_RULE')}</p>
            <p><strong>Category:</strong> {risk.get('category', 'uncategorized')}</p>
            <p><strong>Components:</strong> {components}</p>
            <p><strong>Nets:</strong> {nets}</p>
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
            background: #f3f4f6;
            color: #111827;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 32px;
        }
        .hero {
            background: #111827;
            color: white;
            padding: 28px;
            border-radius: 16px;
            margin-bottom: 24px;
        }
        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
        }
        .card {
            background: white;
            padding: 24px;
            border-radius: 16px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        }
        .recent-run {
            padding: 14px;
            border: 1px solid #e5e7eb;
            border-radius: 10px;
            margin-bottom: 12px;
        }
        input[type=file] {
            margin: 12px 0;
            width: 100%;
        }
        button {
            background: #111827;
            color: white;
            border: none;
            padding: 12px 18px;
            border-radius: 10px;
            cursor: pointer;
        }
        button:hover {
            opacity: 0.92;
        }
        a {
            color: #2563eb;
            text-decoration: none;
        }
        .note {
            color: #6b7280;
            font-size: 14px;
        }
        @media (max-width: 900px) {
            .grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="hero">
            <h1>Silicore Dashboard</h1>
            <p>PCB risk analysis, project ranking, explainable scoring, and downloadable reports.</p>
        </div>

        <div class="grid">
            <div class="card">
                <h2>Single Board Analysis</h2>
                <form action="/analyze" method="post" enctype="multipart/form-data">
                    <input type="file" name="board_file" required>
                    <button type="submit">Analyze Board</button>
                </form>
                <p class="note">Upload one board file. Supports .txt and .kicad_pcb inputs.</p>
            </div>

            <div class="card">
                <h2>Project Analysis</h2>
                <form action="/project" method="post" enctype="multipart/form-data">
                    <input type="file" name="board_files" multiple required>
                    <button type="submit">Analyze Project</button>
                </form>
                <p class="note">Select all project files at once. Rank 1 is best. Higher rank is worse.</p>
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
            background: #f3f4f6;
            color: #111827;
        }
        .container {
            max-width: 1100px;
            margin: 0 auto;
            padding: 32px;
        }
        .card, .score-box, .risk-card {
            background: white;
            padding: 22px;
            border-radius: 14px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
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
        .top-links {
            margin-bottom: 20px;
        }
        .summary-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 18px;
        }
        @media (max-width: 900px) {
            .summary-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="top-links">
            <a href="/">← Back to Dashboard</a>
        </div>

        <div class="card">
            <h1>Single Board Result</h1>
            <p><strong>Board:</strong> {{ board_name }}</p>
            <p><strong>Overall Risk Score:</strong> {{ score }} / 10</p>
            <p><strong>Total Risks:</strong> {{ total_risks }}</p>
            <p>
                <a href="/download/{{ run_id }}/json">Download JSON</a> |
                <a href="/download/{{ run_id }}/markdown">Download Markdown</a> |
                <a href="/download/{{ run_id }}/html">Download HTML</a>
            </p>
        </div>

        <div class="summary-grid">
            <div class="card">
                <h3>Severity Summary</h3>
                <ul>
                    <li>Low: {{ by_severity.get('low', 0) }}</li>
                    <li>Medium: {{ by_severity.get('medium', 0) }}</li>
                    <li>High: {{ by_severity.get('high', 0) }}</li>
                    <li>Critical: {{ by_severity.get('critical', 0) }}</li>
                </ul>
            </div>

            <div class="card">
                <h3>Category Summary</h3>
                {% if by_category %}
                    <ul>
                        {% for category, count in by_category.items() %}
                            <li>{{ category }}: {{ count }}</li>
                        {% endfor %}
                    </ul>
                {% else %}
                    <p>No category risks found.</p>
                {% endif %}
            </div>
        </div>

        {{ score_explanation_html|safe }}

        <div class="card">
            <h2>Detailed Findings</h2>
            {{ risk_list_html|safe }}
        </div>
    </div>
</body>
</html>
        """,
        board_name=filename,
        score=analysis_result.get("score", 0),
        total_risks=risk_summary.get("total_risks", 0),
        by_severity=risk_summary.get("by_severity", {}),
        by_category=risk_summary.get("by_category", {}),
        score_explanation_html=score_explanation_html,
        risk_list_html=risk_list_html,
        run_id=run_id,
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
            board["badge"] = "Best Board" if index == 1 else (
                "Worst Board" if index == len(board_results) else ""
            )

        run_id, _ = create_project_run(board_results)

    except Exception as exc:
        shutil.rmtree(temp_dir, ignore_errors=True)
        return f"<h2>Project analysis failed</h2><p>{exc}</p>", 500

    shutil.rmtree(temp_dir, ignore_errors=True)

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
            background: #f3f4f6;
            color: #111827;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 32px;
        }
        .board-card, .summary-card, .score-box, .risk-card {
            background: white;
            padding: 22px;
            border-radius: 14px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
            margin-bottom: 20px;
        }
        .badge {
            display: inline-block;
            background: #111827;
            color: white;
            padding: 6px 10px;
            border-radius: 999px;
            font-size: 12px;
            margin-left: 8px;
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
        .rank {
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 8px;
        }
        .summary-grid {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 18px;
            margin-bottom: 24px;
        }
        @media (max-width: 900px) {
            .summary-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="top-links">
            <a href="/">← Back to Dashboard</a>
        </div>

        <div class="summary-card">
            <h1>Project Results</h1>
            <p><strong>Board Count:</strong> {{ board_count }}</p>
            <p><strong>Ranking:</strong> 1 is best, higher number is worse</p>
            <p>
                <a href="/download/{{ run_id }}/json">Download JSON</a> |
                <a href="/download/{{ run_id }}/markdown">Download Markdown</a> |
                <a href="/download/{{ run_id }}/html">Download HTML</a>
            </p>
        </div>

        {% for board in board_results %}
            <div class="board-card">
                <div class="rank">
                    Rank {{ board.rank }} — {{ board.board_name }}
                    {% if board.badge %}
                        <span class="badge">{{ board.badge }}</span>
                    {% endif %}
                </div>

                <div class="summary-grid">
                    <div class="summary-card">
                        <h3>Board Score</h3>
                        <p><strong>{{ board.score }}</strong> / 10</p>
                    </div>

                    <div class="summary-card">
                        <h3>Total Risks</h3>
                        <p><strong>{{ board.risk_summary.get('total_risks', 0) }}</strong></p>
                    </div>

                    <div class="summary-card">
                        <h3>Severity Summary</h3>
                        <ul>
                            <li>Low: {{ board.risk_summary.get('by_severity', {}).get('low', 0) }}</li>
                            <li>Medium: {{ board.risk_summary.get('by_severity', {}).get('medium', 0) }}</li>
                            <li>High: {{ board.risk_summary.get('by_severity', {}).get('high', 0) }}</li>
                            <li>Critical: {{ board.risk_summary.get('by_severity', {}).get('critical', 0) }}</li>
                        </ul>
                    </div>
                </div>

                <div class="summary-card">
                    <h3>Category Summary</h3>
                    {% if board.risk_summary.get('by_category', {}) %}
                        <ul>
                            {% for category, count in board.risk_summary.get('by_category', {}).items() %}
                                <li>{{ category }}: {{ count }}</li>
                            {% endfor %}
                        </ul>
                    {% else %}
                        <p>No category risks found.</p>
                    {% endif %}
                </div>

                {{ build_score_explanation_html(board.score_explanation)|safe }}

                <div class="summary-card">
                    <h3>Detailed Findings</h3>
                    {{ build_risk_list_html(board.risks)|safe }}
                </div>
            </div>
        {% endfor %}
    </div>
</body>
</html>
        """,
        board_results=board_results,
        board_count=len(board_results),
        run_id=run_id,
        build_score_explanation_html=build_score_explanation_html,
        build_risk_list_html=build_risk_list_html,
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