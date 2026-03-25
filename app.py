import os
import tempfile
from datetime import datetime

from flask import Flask, request, render_template_string, send_file, abort, url_for

from engine.parser import start_engine, parse_pcb_file
from engine.kicad_parser import parse_kicad_file
from engine.normalizer import normalize_pcb
from engine.rule_runner import run_analysis
from engine.report_generator import generate_report
from engine.config_loader import load_config
from engine.project_analyzer import build_board_result, summarize_project
from engine.dashboard_storage import (
    save_single_run,
    save_project_run,
    list_recent_runs,
    get_download_path,
)

app = Flask(__name__)
start_engine()
CONFIG = load_config()

SUPPORTED_EXTENSIONS = {".kicad_pcb", ".txt"}

HTML = """
<!doctype html>
<html>
<head>
    <title>Silicore Dashboard</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            background: #f4f7fb;
            color: #1f2937;
        }

        .page {
            max-width: 1280px;
            margin: 0 auto;
            padding: 32px;
        }

        .hero {
            background: linear-gradient(135deg, #0f172a, #1e293b);
            color: white;
            padding: 28px;
            border-radius: 16px;
            margin-bottom: 24px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.12);
        }

        .hero h1 {
            margin: 0 0 8px 0;
            font-size: 34px;
        }

        .hero p {
            margin: 0;
            opacity: 0.9;
        }

        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 24px;
        }

        .card {
            background: white;
            border-radius: 16px;
            padding: 22px;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
        }

        .card h2 {
            margin-top: 0;
            margin-bottom: 14px;
            font-size: 22px;
        }

        .muted {
            color: #64748b;
            font-size: 14px;
        }

        .form-row {
            margin-bottom: 14px;
        }

        .form-row label {
            display: block;
            font-weight: bold;
            margin-bottom: 6px;
        }

        input[type=file] {
            width: 100%;
            padding: 10px;
            background: #f8fafc;
            border: 1px solid #cbd5e1;
            border-radius: 10px;
            box-sizing: border-box;
        }

        button {
            border: none;
            background: #0f172a;
            color: white;
            padding: 12px 18px;
            border-radius: 10px;
            cursor: pointer;
            font-weight: bold;
        }

        button:hover {
            background: #1e293b;
        }

        .error {
            background: #fee2e2;
            color: #991b1b;
            padding: 14px 16px;
            border-radius: 12px;
            margin-bottom: 20px;
            font-weight: bold;
            white-space: pre-wrap;
        }

        .success {
            background: #dcfce7;
            color: #166534;
            padding: 14px 16px;
            border-radius: 12px;
            margin-bottom: 20px;
            font-weight: bold;
        }

        .summary-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin-bottom: 24px;
        }

        .summary-box {
            background: white;
            border-radius: 16px;
            padding: 18px;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
        }

        .summary-box .label {
            font-size: 13px;
            color: #64748b;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }

        .summary-box .value {
            font-size: 28px;
            font-weight: bold;
        }

        .section {
            margin-bottom: 24px;
        }

        .section-title {
            margin: 0 0 14px 0;
            font-size: 24px;
        }

        .pill-list {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }

        .pill {
            background: #e2e8f0;
            color: #0f172a;
            padding: 8px 12px;
            border-radius: 999px;
            font-size: 14px;
            font-weight: bold;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
        }

        th, td {
            padding: 14px 16px;
            text-align: left;
            border-bottom: 1px solid #e5e7eb;
        }

        th {
            background: #f8fafc;
            font-size: 14px;
            text-transform: uppercase;
            color: #475569;
        }

        tr:last-child td {
            border-bottom: none;
        }

        .score-bad {
            color: #991b1b;
            font-weight: bold;
        }

        .score-medium {
            color: #a16207;
            font-weight: bold;
        }

        .score-good {
            color: #166534;
            font-weight: bold;
        }

        .board-card {
            background: white;
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
            margin-bottom: 18px;
        }

        .board-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 16px;
            margin-bottom: 12px;
            flex-wrap: wrap;
        }

        .board-header h3 {
            margin: 0;
            font-size: 22px;
        }

        .stats {
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
            margin-bottom: 14px;
        }

        .stat {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 999px;
            padding: 8px 12px;
            font-size: 14px;
            font-weight: bold;
        }

        .risk {
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 14px;
            margin-bottom: 12px;
            background: #fcfcfd;
        }

        .risk:last-child {
            margin-bottom: 0;
        }

        .risk-message {
            font-weight: bold;
            margin-bottom: 8px;
        }

        .sev-critical {
            color: #7f1d1d;
            font-weight: bold;
        }

        .sev-high {
            color: #b91c1c;
            font-weight: bold;
        }

        .sev-medium {
            color: #a16207;
            font-weight: bold;
        }

        .sev-low {
            color: #166534;
            font-weight: bold;
        }

        .download-row {
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
            margin-bottom: 20px;
        }

        .download-link {
            display: inline-block;
            background: #0f172a;
            color: white;
            text-decoration: none;
            padding: 10px 14px;
            border-radius: 10px;
            font-weight: bold;
        }

        .download-link:hover {
            background: #1e293b;
        }

        .recent-run {
            display: flex;
            justify-content: space-between;
            gap: 16px;
            padding: 14px 0;
            border-bottom: 1px solid #e5e7eb;
            flex-wrap: wrap;
        }

        .recent-run:last-child {
            border-bottom: none;
        }

        .recent-run-title {
            font-weight: bold;
        }

        .recent-run-meta {
            color: #64748b;
            font-size: 14px;
        }

        .recent-run-links {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }

        .recent-run-links a {
            color: #0f172a;
            font-weight: bold;
            text-decoration: none;
        }

        .recent-run-links a:hover {
            text-decoration: underline;
        }

        pre {
            background: #0f172a;
            color: #e2e8f0;
            padding: 18px;
            border-radius: 14px;
            white-space: pre-wrap;
            overflow-x: auto;
        }

        @media (max-width: 1000px) {
            .grid {
                grid-template-columns: 1fr;
            }

            .summary-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }

        @media (max-width: 640px) {
            .summary-grid {
                grid-template-columns: 1fr;
            }

            .page {
                padding: 18px;
            }
        }
    </style>
</head>
<body>
    <div class="page">
        <div class="hero">
            <h1>Silicore Dashboard</h1>
            <p>AI-powered hardware design intelligence for single-board analysis and project-level PCB review</p>
        </div>

        {% if error %}
            <div class="error">{{ error }}</div>
        {% endif %}

        {% if success %}
            <div class="success">{{ success }}</div>
        {% endif %}

        <div class="grid">
            <div class="card">
                <h2>Single Board Analysis</h2>
                <p class="muted">Upload one .kicad_pcb or .txt PCB file and generate a full engineering report.</p>
                <form method="post" enctype="multipart/form-data">
                    <input type="hidden" name="form_type" value="single">
                    <div class="form-row">
                        <label for="single_file">PCB File</label>
                        <input type="file" id="single_file" name="pcb_file" required>
                    </div>
                    <button type="submit">Analyze Single Board</button>
                </form>
            </div>

            <div class="card">
                <h2>Project Batch Analysis</h2>
                <p class="muted">Select all files at once. On Mac, hold Command to choose multiple files.</p>
                <form method="post" enctype="multipart/form-data">
                    <input type="hidden" name="form_type" value="project">
                    <div class="form-row">
                        <label for="project_files">Project Files</label>
                        <input type="file" id="project_files" name="project_files" multiple required>
                    </div>
                    <button type="submit">Analyze Project</button>
                </form>
            </div>
        </div>

        {% if download_bundle %}
            <div class="card" style="margin-bottom: 24px;">
                <h2>Downloads</h2>
                <div class="download-row">
                    <a class="download-link" href="{{ url_for('download_run_file', run_id=download_bundle['run_id'], filename=download_bundle['json_filename']) }}">Download JSON</a>
                    <a class="download-link" href="{{ url_for('download_run_file', run_id=download_bundle['run_id'], filename=download_bundle['md_filename']) }}">Download Markdown</a>
                    <a class="download-link" href="{{ url_for('download_run_file', run_id=download_bundle['run_id'], filename=download_bundle['html_filename']) }}">Download HTML</a>
                </div>
            </div>
        {% endif %}

        {% if single_result %}
            <div class="section">
                <h2 class="section-title">Single Board Result</h2>

                <div class="summary-grid">
                    <div class="summary-box">
                        <div class="label">Board</div>
                        <div class="value" style="font-size: 20px;">{{ single_result["board_name"] }}</div>
                    </div>
                    <div class="summary-box">
                        <div class="label">Score</div>
                        <div class="value">{{ single_result["score"] }}</div>
                    </div>
                    <div class="summary-box">
                        <div class="label">Risks</div>
                        <div class="value">{{ single_result["risk_count"] }}</div>
                    </div>
                    <div class="summary-box">
                        <div class="label">Components</div>
                        <div class="value">{{ single_result["component_count"] }}</div>
                    </div>
                </div>

                <div class="card">
                    <h2>Generated Report</h2>
                    <pre>{{ single_result["report"] }}</pre>
                </div>
            </div>
        {% endif %}

        {% if project_summary %}
            <div class="section">
                <h2 class="section-title">Project Summary</h2>

                <div class="summary-grid">
                    <div class="summary-box">
                        <div class="label">Boards Analyzed</div>
                        <div class="value">{{ project_summary["boards_analyzed"] }}</div>
                    </div>
                    <div class="summary-box">
                        <div class="label">Average Score</div>
                        <div class="value">{{ project_summary["average_score"] }}</div>
                    </div>
                    <div class="summary-box">
                        <div class="label">Total Risks</div>
                        <div class="value">{{ project_summary["total_risks"] }}</div>
                    </div>
                    <div class="summary-box">
                        <div class="label">Low Scoring Boards</div>
                        <div class="value">{{ project_summary["boards_below_threshold_5"]|length }}</div>
                    </div>
                </div>

                <div class="grid">
                    <div class="card">
                        <h2>Top Risk Categories</h2>
                        <div class="pill-list">
                            {% for category, count in top_categories %}
                                <div class="pill">{{ category }}: {{ count }}</div>
                            {% endfor %}
                        </div>
                    </div>

                    <div class="card">
                        <h2>Severity Breakdown</h2>
                        <div class="pill-list">
                            {% for severity, count in severity_breakdown %}
                                <div class="pill">{{ severity }}: {{ count }}</div>
                            {% endfor %}
                        </div>
                    </div>
                </div>

                <div class="section">
                    <h2 class="section-title">Board Ranking</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>Rank</th>
                                <th>Board</th>
                                <th>Score</th>
                                <th>Risks</th>
                                <th>Components</th>
                                <th>Nets</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for board in ranked_boards %}
                                <tr>
                                    <td>{{ loop.index }}</td>
                                    <td>{{ board["board_name"] }}</td>
                                    <td>
                                        <span class="{% if board['score'] < 5 %}score-bad{% elif board['score'] < 7 %}score-medium{% else %}score-good{% endif %}">
                                            {{ board["score"] }}
                                        </span>
                                    </td>
                                    <td>{{ board["risk_count"] }}</td>
                                    <td>{{ board["component_count"] }}</td>
                                    <td>{{ board["net_count"] }}</td>
                                </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>

                <div class="section">
                    <h2 class="section-title">Detailed Board Findings</h2>
                    {% for board in ranked_boards %}
                        <div class="board-card">
                            <div class="board-header">
                                <h3>{{ board["board_name"] }}</h3>
                                <div class="{% if board['score'] < 5 %}score-bad{% elif board['score'] < 7 %}score-medium{% else %}score-good{% endif %}">
                                    Score: {{ board["score"] }} / 10
                                </div>
                            </div>

                            <div class="stats">
                                <div class="stat">Risks: {{ board["risk_count"] }}</div>
                                <div class="stat">Components: {{ board["component_count"] }}</div>
                                <div class="stat">Nets: {{ board["net_count"] }}</div>
                            </div>

                            {% if board["risks"] %}
                                {% for risk in board["risks"] %}
                                    <div class="risk">
                                        <div class="risk-message">
                                            <span class="sev-{{ risk['severity'] }}">[{{ risk['severity']|upper }}]</span>
                                            {{ risk["message"] }}
                                        </div>
                                        <div><strong>Category:</strong> {{ risk["category"] }}</div>
                                        <div><strong>Recommendation:</strong> {{ risk["recommendation"] }}</div>
                                        <div><strong>Confidence:</strong> {{ risk["confidence"] }}</div>
                                        {% if risk["why_it_matters"] %}
                                            <div><strong>Why it matters:</strong> {{ risk["why_it_matters"] }}</div>
                                        {% endif %}
                                        {% if risk["components"] %}
                                            <div><strong>Components:</strong> {{ risk["components"]|join(", ") }}</div>
                                        {% endif %}
                                        {% if risk["nets"] %}
                                            <div><strong>Nets:</strong> {{ risk["nets"]|join(", ") }}</div>
                                        {% endif %}
                                        {% if risk["metrics"] %}
                                            <div><strong>Metrics:</strong> {{ risk["metrics"] }}</div>
                                        {% endif %}
                                    </div>
                                {% endfor %}
                            {% else %}
                                <div class="risk">
                                    No risks detected for this board.
                                </div>
                            {% endif %}
                        </div>
                    {% endfor %}
                </div>

                <div class="card">
                    <h2>Project Summary Report</h2>
                    <pre>{{ project_report }}</pre>
                </div>
            </div>
        {% endif %}

        <div class="card">
            <h2>Recent Saved Runs</h2>
            {% if recent_runs %}
                {% for run in recent_runs %}
                    <div class="recent-run">
                        <div>
                            <div class="recent-run-title">{{ run["title"] }}</div>
                            <div class="recent-run-meta">
                                {{ run["run_type"]|upper }} |
                                {{ run["created_at"] }}
                            </div>
                        </div>
                        <div class="recent-run-links">
                            <a href="{{ url_for('download_run_file', run_id=run['run_id'], filename=run['files']['json'].split('/')[-1]) }}">JSON</a>
                            <a href="{{ url_for('download_run_file', run_id=run['run_id'], filename=run['files']['md'].split('/')[-1]) }}">Markdown</a>
                            <a href="{{ url_for('download_run_file', run_id=run['run_id'], filename=run['files']['html'].split('/')[-1]) }}">HTML</a>
                        </div>
                    </div>
                {% endfor %}
            {% else %}
                <div class="muted">No saved runs yet.</div>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""


def is_supported_file(filename):
    if not filename:
        return False
    extension = os.path.splitext(filename)[1].lower()
    return extension in SUPPORTED_EXTENSIONS


def load_pcb(filename):
    if filename.endswith(".kicad_pcb"):
        pcb = parse_kicad_file(filename)
    else:
        pcb = parse_pcb_file(filename)

    pcb = normalize_pcb(pcb)
    return pcb


def make_unique_filename(directory, filename):
    safe_name = os.path.basename(filename)
    base, ext = os.path.splitext(safe_name)
    candidate = safe_name
    counter = 1

    while os.path.exists(os.path.join(directory, candidate)):
        candidate = f"{base}_{counter}{ext}"
        counter += 1

    return candidate


def save_uploaded_file(uploaded_file, directory):
    unique_name = make_unique_filename(directory, uploaded_file.filename)
    destination = os.path.join(directory, unique_name)
    uploaded_file.save(destination)
    return destination


def analyze_single_file(file_path):
    pcb = load_pcb(file_path)
    risks, score = run_analysis(pcb, config=CONFIG)
    report = generate_report(pcb, risks, score)

    result = build_board_result(file_path, pcb, risks, score)
    result["report"] = report
    return result


def generate_project_summary_report(board_results, project_summary):
    lines = []
    lines.append("SILICORE PROJECT SUMMARY")
    lines.append("=" * 60)
    lines.append(f"Boards analyzed: {project_summary['boards_analyzed']}")
    lines.append(f"Average score: {project_summary['average_score']} / 10")
    lines.append(f"Total components: {project_summary['total_components']}")
    lines.append(f"Total nets: {project_summary['total_nets']}")
    lines.append(f"Total risks: {project_summary['total_risks']}")
    lines.append("")

    if project_summary["best_board"]:
        lines.append("BEST BOARD")
        lines.append("-" * 60)
        lines.append(
            f"{project_summary['best_board']['board_name']} | "
            f"Score: {project_summary['best_board']['score']} | "
            f"Risks: {project_summary['best_board']['risk_count']}"
        )
        lines.append("")

    if project_summary["worst_board"]:
        lines.append("WORST BOARD")
        lines.append("-" * 60)
        lines.append(
            f"{project_summary['worst_board']['board_name']} | "
            f"Score: {project_summary['worst_board']['score']} | "
            f"Risks: {project_summary['worst_board']['risk_count']}"
        )
        lines.append("")

    lines.append("RISK CATEGORIES")
    lines.append("-" * 60)
    if project_summary["risk_categories"]:
        sorted_categories = sorted(
            project_summary["risk_categories"].items(),
            key=lambda item: item[1],
            reverse=True,
        )
        for category, count in sorted_categories:
            lines.append(f"{category}: {count}")
    else:
        lines.append("No categories found.")
    lines.append("")

    lines.append("RISK SEVERITIES")
    lines.append("-" * 60)
    if project_summary["risk_severities"]:
        severity_order = ["critical", "high", "medium", "low", "unknown"]
        sorted_severities = sorted(
            project_summary["risk_severities"].items(),
            key=lambda item: severity_order.index(item[0]) if item[0] in severity_order else 99,
        )
        for severity, count in sorted_severities:
            lines.append(f"{severity}: {count}")
    else:
        lines.append("No severities found.")
    lines.append("")

    lines.append("PER-BOARD RESULTS")
    lines.append("-" * 60)
    for board in sorted(board_results, key=lambda item: item["score"], reverse=True):
        lines.append(
            f"{board['board_name']} | "
            f"Score: {board['score']} | "
            f"Risks: {board['risk_count']} | "
            f"Components: {board['component_count']} | "
            f"Nets: {board['net_count']}"
        )

    return "\n".join(lines)


def analyze_project_files(file_paths):
    board_results = []

    for file_path in file_paths:
        pcb = load_pcb(file_path)
        risks, score = run_analysis(pcb, config=CONFIG)
        board_result = build_board_result(file_path, pcb, risks, score)
        board_results.append(board_result)

    ranked_boards = sorted(board_results, key=lambda item: item["score"], reverse=True)
    project_summary = summarize_project(board_results)
    project_report = generate_project_summary_report(board_results, project_summary)

    top_categories = sorted(
        project_summary["risk_categories"].items(),
        key=lambda item: item[1],
        reverse=True,
    )

    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "unknown": 4}
    severity_breakdown = sorted(
        project_summary["risk_severities"].items(),
        key=lambda item: severity_order.get(item[0], 99),
    )

    return ranked_boards, project_summary, project_report, top_categories, severity_breakdown


@app.route("/", methods=["GET", "POST"])
def home():
    error = None
    success = None
    single_result = None
    project_summary = None
    project_report = None
    ranked_boards = []
    top_categories = []
    severity_breakdown = []
    download_bundle = None

    if request.method == "POST":
        form_type = request.form.get("form_type", "").strip()

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                if form_type == "single":
                    uploaded = request.files.get("pcb_file")

                    if not uploaded or not uploaded.filename:
                        error = "Please upload a PCB file for single-board analysis."
                    elif not is_supported_file(uploaded.filename):
                        error = "Unsupported file type. Use .kicad_pcb or .txt"
                    else:
                        file_path = save_uploaded_file(uploaded, temp_dir)
                        single_result = analyze_single_file(file_path)
                        download_bundle = save_single_run(single_result)
                        success = f"Single-board analysis completed for {single_result['board_name']}."

                elif form_type == "project":
                    uploaded_files = request.files.getlist("project_files")

                    valid_files = []
                    skipped_files = []

                    for uploaded in uploaded_files:
                        if uploaded and uploaded.filename:
                            if is_supported_file(uploaded.filename):
                                valid_files.append(uploaded)
                            else:
                                skipped_files.append(uploaded.filename)

                    if not valid_files:
                        error = "Please upload one or more supported project files (.kicad_pcb or .txt)."
                    else:
                        file_paths = [save_uploaded_file(uploaded, temp_dir) for uploaded in valid_files]

                        (
                            ranked_boards,
                            project_summary,
                            project_report,
                            top_categories,
                            severity_breakdown,
                        ) = analyze_project_files(file_paths)

                        download_bundle = save_project_run(ranked_boards, project_summary, project_report)
                        success = f"Project analysis completed for {project_summary['boards_analyzed']} board(s)."

                        if skipped_files:
                            success += f" Skipped unsupported files: {', '.join(skipped_files)}"

                else:
                    error = "Unknown analysis request."

        except Exception as e:
            error = f"Analysis failed: {e}"

    recent_runs = list_recent_runs(limit=10)

    return render_template_string(
        HTML,
        error=error,
        success=success,
        single_result=single_result,
        project_summary=project_summary,
        project_report=project_report,
        ranked_boards=ranked_boards,
        top_categories=top_categories,
        severity_breakdown=severity_breakdown,
        download_bundle=download_bundle,
        recent_runs=recent_runs,
        url_for=url_for,
        now=datetime.now().isoformat(),
    )


@app.route("/download/<run_id>/<filename>")
def download_run_file(run_id, filename):
    safe_filename = os.path.basename(filename)
    file_path = get_download_path(run_id, safe_filename)

    if not file_path:
        abort(404)

    return send_file(file_path, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)