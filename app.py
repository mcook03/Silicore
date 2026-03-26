import os

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

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Silicore Dashboard</title>
    <style>
        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: #0f172a;
            color: #e2e8f0;
        }

        .container {
            width: 95%;
            max-width: 1400px;
            margin: 0 auto;
            padding: 24px 0 48px;
        }

        .hero {
            background: linear-gradient(135deg, #111827, #1e293b);
            border: 1px solid #334155;
            border-radius: 18px;
            padding: 28px;
            margin-bottom: 24px;
        }

        .hero h1 {
            margin: 0 0 8px;
            font-size: 34px;
        }

        .hero p {
            margin: 0;
            color: #cbd5e1;
            line-height: 1.6;
        }

        .dev-note {
            margin-top: 14px;
            display: inline-block;
            padding: 8px 12px;
            border-radius: 999px;
            background: #1e293b;
            border: 1px solid #475569;
            color: #93c5fd;
            font-size: 13px;
        }

        .grid {
            display: grid;
            grid-template-columns: 1.1fr 1.1fr 1fr;
            gap: 20px;
            align-items: start;
        }

        .card {
            background: #111827;
            border: 1px solid #334155;
            border-radius: 18px;
            padding: 22px;
            box-shadow: 0 12px 30px rgba(0, 0, 0, 0.22);
        }

        .card h2 {
            margin-top: 0;
            font-size: 22px;
        }

        .card h3 {
            margin-top: 0;
            font-size: 18px;
        }

        .muted {
            color: #94a3b8;
        }

        label {
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
            color: #e2e8f0;
        }

        input[type="file"],
        input[type="text"],
        input[type="number"],
        select {
            width: 100%;
            padding: 12px;
            border-radius: 10px;
            border: 1px solid #475569;
            background: #0f172a;
            color: #e2e8f0;
            margin-bottom: 16px;
        }

        button {
            border: none;
            border-radius: 10px;
            padding: 12px 16px;
            font-weight: bold;
            cursor: pointer;
            background: #2563eb;
            color: white;
        }

        button:hover {
            background: #1d4ed8;
        }

        .flash {
            margin-bottom: 16px;
            padding: 14px 16px;
            border-radius: 12px;
            border: 1px solid #475569;
            background: #1e293b;
        }

        .summary-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 14px;
            margin-top: 18px;
        }

        .summary-box {
            background: #0f172a;
            border: 1px solid #334155;
            border-radius: 14px;
            padding: 16px;
        }

        .summary-box .label {
            color: #94a3b8;
            font-size: 13px;
            margin-bottom: 8px;
        }

        .summary-box .value {
            font-size: 22px;
            font-weight: bold;
        }

        .config-section {
            margin-bottom: 18px;
            padding: 16px;
            border-radius: 14px;
            background: #0f172a;
            border: 1px solid #334155;
        }

        .config-section-title {
            margin: 0 0 12px;
            font-size: 16px;
            color: #93c5fd;
        }

        .two-col {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 14px;
        }

        .results {
            margin-top: 26px;
        }

        .result-card {
            background: #111827;
            border: 1px solid #334155;
            border-radius: 18px;
            padding: 22px;
            margin-bottom: 18px;
        }

        .pill {
            display: inline-block;
            padding: 6px 10px;
            border-radius: 999px;
            margin-right: 8px;
            margin-bottom: 8px;
            font-size: 12px;
            font-weight: bold;
            border: 1px solid #475569;
            background: #1e293b;
        }

        .risk-item {
            border-top: 1px solid #334155;
            padding-top: 14px;
            margin-top: 14px;
        }

        .badge-best {
            background: #14532d;
            border-color: #22c55e;
        }

        .badge-worst {
            background: #7f1d1d;
            border-color: #ef4444;
        }

        .run-list a,
        .download-links a {
            color: #93c5fd;
            text-decoration: none;
        }

        .run-list a:hover,
        .download-links a:hover {
            text-decoration: underline;
        }

        .run-meta {
            color: #94a3b8;
            font-size: 13px;
            margin-top: 4px;
        }

        .footer-note {
            margin-top: 18px;
            color: #94a3b8;
            font-size: 13px;
        }

        @media (max-width: 1100px) {
            .grid {
                grid-template-columns: 1fr;
            }

            .summary-grid {
                grid-template-columns: 1fr 1fr;
            }

            .two-col {
                grid-template-columns: 1fr;
            }
        }

        @media (max-width: 640px) {
            .summary-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="hero">
            <h1>Silicore</h1>
            <p>AI-powered PCB design intelligence for risk detection, explainability, revision comparison, and project-level analysis.</p>
            <div class="dev-note">Dev build: Local prototype dashboard</div>

            <div class="summary-grid">
                <div class="summary-box">
                    <div class="label">Mode</div>
                    <div class="value">Dashboard</div>
                </div>
                <div class="summary-box">
                    <div class="label">Engine</div>
                    <div class="value">Service Layer</div>
                </div>
                <div class="summary-box">
                    <div class="label">Storage</div>
                    <div class="value">Persistent Runs</div>
                </div>
                <div class="summary-box">
                    <div class="label">Milestone</div>
                    <div class="value">13</div>
                </div>
            </div>
        </div>

        {% with messages = get_flashed_messages() %}
            {% if messages %}
                {% for message in messages %}
                    <div class="flash">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        <div class="grid">
            <div class="card">
                <h2>Single Board Analysis</h2>
                <p class="muted">Upload one board file for immediate analysis.</p>
                <form action="/analyze" method="post" enctype="multipart/form-data">
                    <label for="single_file">Board File</label>
                    <input type="file" id="single_file" name="single_file" required>
                    <button type="submit">Analyze Board</button>
                </form>
            </div>

            <div class="card">
                <h2>Project Analysis</h2>
                <p class="muted">Upload multiple files at once to compare boards and rank them. On Mac, hold Command to select multiple files.</p>
                <form action="/analyze_project" method="post" enctype="multipart/form-data">
                    <label for="project_files">Project Files</label>
                    <input type="file" id="project_files" name="project_files" multiple required>
                    <button type="submit">Analyze Project</button>
                </form>
            </div>

            <div class="card">
                <h2>Config Editor</h2>
                <p class="muted">Tune the analysis engine without manually editing files.</p>
                <form action="/save_config" method="post">
                    <div class="config-section">
                        <div class="config-section-title">Layout</div>
                        <div class="two-col">
                            <div>
                                <label for="min_component_spacing">Min Component Spacing</label>
                                <input
                                    type="number"
                                    step="0.1"
                                    id="min_component_spacing"
                                    name="min_component_spacing"
                                    value="{{ config.layout.min_component_spacing }}"
                                    required
                                >
                            </div>
                            <div>
                                <label for="density_threshold">Density Threshold</label>
                                <input
                                    type="number"
                                    id="density_threshold"
                                    name="density_threshold"
                                    value="{{ config.layout.density_threshold }}"
                                    required
                                >
                            </div>
                        </div>
                    </div>

                    <div class="config-section">
                        <div class="config-section-title">Power</div>
                        <label for="required_power_nets">Required Power Nets</label>
                        <input
                            type="text"
                            id="required_power_nets"
                            name="required_power_nets"
                            value="{{ config.power.required_power_nets | join(', ') }}"
                            required
                        >

                        <label for="required_ground_nets">Required Ground Nets</label>
                        <input
                            type="text"
                            id="required_ground_nets"
                            name="required_ground_nets"
                            value="{{ config.power.required_ground_nets | join(', ') }}"
                            required
                        >
                    </div>

                    <div class="config-section">
                        <div class="config-section-title">Signal</div>
                        <label for="max_trace_length">Max Trace Length</label>
                        <input
                            type="number"
                            step="0.1"
                            id="max_trace_length"
                            name="max_trace_length"
                            value="{{ config.signal.max_trace_length }}"
                            required
                        >

                        <label for="critical_nets">Critical Nets</label>
                        <input
                            type="text"
                            id="critical_nets"
                            name="critical_nets"
                            value="{{ config.signal.critical_nets | join(', ') }}"
                            required
                        >
                    </div>

                    <button type="submit">Save Config</button>
                </form>
            </div>
        </div>

        <div class="results">
            {% if result %}
                <div class="result-card">
                    <h2>Single Board Result</h2>
                    <p><strong>File:</strong> {{ result.filename }}</p>
                    <p><strong>Score:</strong> {{ result.score }} / 10</p>

                    {% if result.score_explanation %}
                        <h3>Score Explanation</h3>
                        <p><strong>Start Score:</strong> {{ result.score_explanation.start_score }}</p>
                        <p><strong>Total Penalty:</strong> {{ result.score_explanation.total_penalty }}</p>

                        {% if result.score_explanation.severity_totals %}
                            <h4>Severity Penalties</h4>
                            {% for severity, penalty in result.score_explanation.severity_totals.items() %}
                                <span class="pill">{{ severity }}: {{ penalty }}</span>
                            {% endfor %}
                        {% endif %}

                        {% if result.score_explanation.category_totals %}
                            <h4 style="margin-top: 16px;">Category Penalties</h4>
                            {% for category, penalty in result.score_explanation.category_totals.items() %}
                                <span class="pill">{{ category }}: {{ penalty }}</span>
                            {% endfor %}
                        {% endif %}
                    {% endif %}

                    <h3 style="margin-top: 20px;">Detailed Findings</h3>
                    {% if result.risks %}
                        {% for risk in result.risks %}
                            <div class="risk-item">
                                <p><strong>Severity:</strong> {{ risk.severity }}</p>
                                <p><strong>Category:</strong> {{ risk.category }}</p>
                                <p><strong>Message:</strong> {{ risk.message }}</p>
                                <p><strong>Recommendation:</strong> {{ risk.recommendation }}</p>
                            </div>
                        {% endfor %}
                    {% else %}
                        <p>No risks detected.</p>
                    {% endif %}

                    {% if result.downloads %}
                        <div class="download-links">
                            <h3>Downloads</h3>
                            {% for item in result.downloads %}
                                <p><a href="{{ item.url }}">{{ item.label }}</a></p>
                            {% endfor %}
                        </div>
                    {% endif %}
                </div>
            {% endif %}

            {% if project_result %}
                <div class="result-card">
                    <h2>Project Result</h2>

                    {% if project_result.boards %}
                        {% for board in project_result.boards %}
                            <div class="risk-item">
                                <p>
                                    <strong>#{{ board.rank }} — {{ board.filename }}</strong>
                                    {% if board.rank == 1 %}
                                        <span class="pill badge-best">Best Board</span>
                                    {% endif %}
                                    {% if board.rank == project_result.boards|length %}
                                        <span class="pill badge-worst">Worst Board</span>
                                    {% endif %}
                                </p>

                                <p><strong>Score:</strong> {{ board.score }} / 10</p>

                                {% if board.score_explanation %}
                                    <p><strong>Total Penalty:</strong> {{ board.score_explanation.total_penalty }}</p>
                                {% endif %}

                                {% if board.risks %}
                                    {% for risk in board.risks %}
                                        <div class="risk-item">
                                            <p><strong>Severity:</strong> {{ risk.severity }}</p>
                                            <p><strong>Category:</strong> {{ risk.category }}</p>
                                            <p><strong>Message:</strong> {{ risk.message }}</p>
                                            <p><strong>Recommendation:</strong> {{ risk.recommendation }}</p>
                                        </div>
                                    {% endfor %}
                                {% else %}
                                    <p>No risks detected.</p>
                                {% endif %}
                            </div>
                        {% endfor %}
                    {% endif %}

                    {% if project_result.downloads %}
                        <div class="download-links">
                            <h3>Downloads</h3>
                            {% for item in project_result.downloads %}
                                <p><a href="{{ item.url }}">{{ item.label }}</a></p>
                            {% endfor %}
                        </div>
                    {% endif %}
                </div>
            {% endif %}
        </div>

        <div class="card" style="margin-top: 24px;">
            <h2>Recent Saved Runs</h2>
            {% if recent_runs %}
                <div class="run-list">
                    {% for run in recent_runs %}
                        <p>
                            <strong>{{ run.name }}</strong>
                        </p>
                        <div class="run-meta">
                            Type: {{ run.run_type }} |
                            Created: {{ run.created_at }}
                        </div>
                    {% endfor %}
                </div>
            {% else %}
                <p class="muted">No saved runs yet.</p>
            {% endif %}
            <div class="footer-note">Milestone 13 separates dashboard routing from analysis orchestration so Silicore can evolve toward API and SaaS architecture.</div>
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
        recent_runs=get_recent_runs(RUNS_FOLDER)
    )


@app.route("/", methods=["GET"])
def index():
    _, config_view = get_dashboard_config(CONFIG_PATH)
    return render_dashboard(config_view)


@app.route("/save_config", methods=["POST"])
def save_config_route():
    try:
        updated_config = parse_config_form(request.form)
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
            config_path=CONFIG_PATH
        )
        return render_dashboard(
            config=service_result["config_view"],
            result=service_result["result"]
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
            config_path=CONFIG_PATH
        )
        return render_dashboard(
            config=service_result["config_view"],
            project_result=service_result["project_result"]
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
        as_attachment=True
    )


if __name__ == "__main__":
    app.run(debug=True)