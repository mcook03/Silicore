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
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Silicore Dashboard</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    :root {
      --bg-1: #07111f;
      --bg-2: #0d1726;
      --panel: rgba(15, 23, 42, 0.78);
      --panel-strong: rgba(15, 23, 42, 0.92);
      --panel-light: rgba(255, 255, 255, 0.04);
      --border: rgba(148, 163, 184, 0.18);
      --text: #e5eefc;
      --muted: #9fb0c9;
      --accent: #4f8cff;
      --accent-2: #7c3aed;
      --success: #10b981;
      --warning: #f59e0b;
      --danger: #ef4444;
      --shadow: 0 20px 50px rgba(0, 0, 0, 0.35);
      --radius: 18px;
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      font-family: Inter, Arial, sans-serif;
      color: var(--text);
      background:
        radial-gradient(circle at top left, rgba(79, 140, 255, 0.22), transparent 28%),
        radial-gradient(circle at top right, rgba(124, 58, 237, 0.18), transparent 26%),
        linear-gradient(180deg, var(--bg-1), var(--bg-2));
      min-height: 100vh;
    }

    .shell {
      width: min(1380px, calc(100% - 32px));
      margin: 24px auto 40px;
    }

    .hero {
      position: relative;
      overflow: hidden;
      background: linear-gradient(135deg, rgba(79, 140, 255, 0.18), rgba(124, 58, 237, 0.16));
      border: 1px solid var(--border);
      border-radius: 24px;
      padding: 28px;
      box-shadow: var(--shadow);
      backdrop-filter: blur(16px);
      margin-bottom: 22px;
    }

    .hero::after {
      content: "";
      position: absolute;
      right: -80px;
      top: -80px;
      width: 240px;
      height: 240px;
      background: radial-gradient(circle, rgba(79, 140, 255, 0.25), transparent 70%);
      pointer-events: none;
    }

    .hero-top {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 18px;
      flex-wrap: wrap;
    }

    .title-wrap h1 {
      margin: 0 0 8px;
      font-size: 40px;
      letter-spacing: -0.03em;
    }

    .title-wrap p {
      margin: 0;
      max-width: 840px;
      color: var(--muted);
      font-size: 16px;
      line-height: 1.6;
    }

    .milestone-panel {
      min-width: 170px;
      background: rgba(255, 255, 255, 0.06);
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 20px;
      padding: 16px 18px;
      text-align: center;
    }

    .milestone-label {
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.14em;
      margin-bottom: 6px;
    }

    .milestone-value {
      font-size: 40px;
      font-weight: 800;
      line-height: 1;
      margin-bottom: 6px;
    }

    .milestone-sub {
      color: var(--muted);
      font-size: 13px;
    }

    .badge-row {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin-top: 22px;
    }

    .badge {
      padding: 11px 14px;
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.06);
      border: 1px solid rgba(255, 255, 255, 0.09);
      color: #d8e4fb;
      font-size: 13px;
    }

    .grid {
      display: grid;
      grid-template-columns: 1.15fr 0.85fr;
      gap: 22px;
      align-items: start;
    }

    .left-col,
    .right-col {
      display: grid;
      gap: 22px;
    }

    .card {
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 22px;
      box-shadow: var(--shadow);
      backdrop-filter: blur(12px);
    }

    .card h2 {
      margin: 0 0 8px;
      font-size: 22px;
      letter-spacing: -0.02em;
    }

    .card h3 {
      margin: 18px 0 8px;
      font-size: 17px;
      letter-spacing: -0.01em;
    }

    .card p {
      color: var(--muted);
      line-height: 1.6;
      margin: 0 0 10px;
    }

    .section-subtitle {
      color: var(--muted);
      margin-bottom: 16px;
    }

    .form-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 14px;
    }

    .form-grid.full {
      grid-template-columns: 1fr;
    }

    .field {
      display: flex;
      flex-direction: column;
      gap: 7px;
    }

    label {
      color: #d9e5fb;
      font-size: 13px;
      font-weight: 600;
      letter-spacing: 0.02em;
    }

    input[type="text"],
    input[type="number"],
    textarea,
    select {
      width: 100%;
      border: 1px solid rgba(148, 163, 184, 0.2);
      background: rgba(255, 255, 255, 0.05);
      color: var(--text);
      border-radius: 12px;
      padding: 12px 14px;
      outline: none;
      transition: 0.18s ease;
    }

    input[type="text"]:focus,
    input[type="number"]:focus,
    textarea:focus,
    select:focus {
      border-color: rgba(79, 140, 255, 0.7);
      box-shadow: 0 0 0 3px rgba(79, 140, 255, 0.15);
    }

    input[type="file"] {
      width: 100%;
      border: 1px dashed rgba(148, 163, 184, 0.3);
      background: rgba(255, 255, 255, 0.03);
      color: var(--muted);
      border-radius: 14px;
      padding: 14px;
    }

    .button-row {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      margin-top: 12px;
    }

    button {
      border: none;
      border-radius: 12px;
      padding: 12px 16px;
      font-weight: 700;
      cursor: pointer;
      transition: 0.18s ease;
    }

    .primary-btn {
      background: linear-gradient(135deg, var(--accent), #2f6fe8);
      color: white;
    }

    .primary-btn:hover {
      transform: translateY(-1px);
      box-shadow: 0 10px 28px rgba(79, 140, 255, 0.24);
    }

    .secondary-btn {
      background: linear-gradient(135deg, #6d28d9, var(--accent-2));
      color: white;
    }

    .secondary-btn:hover {
      transform: translateY(-1px);
      box-shadow: 0 10px 28px rgba(124, 58, 237, 0.24);
    }

    .flash-wrap {
      display: grid;
      gap: 10px;
      margin-bottom: 22px;
    }

    .flash {
      background: rgba(59, 130, 246, 0.12);
      border: 1px solid rgba(96, 165, 250, 0.24);
      color: #dbeafe;
      padding: 14px 16px;
      border-radius: 14px;
    }

    .metrics {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      gap: 14px;
      margin-top: 18px;
      margin-bottom: 8px;
    }

    .metric {
      background: rgba(255, 255, 255, 0.045);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 16px;
      padding: 16px;
    }

    .metric-label {
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-bottom: 8px;
    }

    .metric-value {
      font-size: 28px;
      font-weight: 800;
      line-height: 1;
    }

    .metric-small {
      color: var(--muted);
      font-size: 13px;
      margin-top: 8px;
    }

    .result-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 16px;
      flex-wrap: wrap;
      margin-bottom: 16px;
    }

    .score-pill {
      min-width: 150px;
      text-align: center;
      border-radius: 18px;
      padding: 14px 16px;
      background: linear-gradient(135deg, rgba(79, 140, 255, 0.18), rgba(124, 58, 237, 0.18));
      border: 1px solid rgba(148, 163, 184, 0.18);
    }

    .score-pill .score-label {
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-bottom: 7px;
    }

    .score-pill .score-value {
      font-size: 34px;
      font-weight: 800;
    }

    .pill-row {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      margin-top: 10px;
    }

    .tiny-pill {
      border-radius: 999px;
      padding: 6px 10px;
      font-size: 12px;
      background: rgba(255, 255, 255, 0.06);
      color: #dbe6fb;
      border: 1px solid rgba(255, 255, 255, 0.08);
    }

    .list-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 14px;
      margin-top: 12px;
    }

    .subpanel {
      background: rgba(255, 255, 255, 0.035);
      border: 1px solid rgba(255, 255, 255, 0.07);
      border-radius: 16px;
      padding: 16px;
    }

    .subpanel ul {
      margin: 0;
      padding-left: 18px;
      color: var(--muted);
    }

    .subpanel li {
      margin-bottom: 6px;
    }

    .risk-card {
      border-radius: 16px;
      padding: 16px;
      margin-top: 12px;
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid rgba(255, 255, 255, 0.08);
    }

    .risk-top {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
      margin-bottom: 10px;
    }

    .risk-tags {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }

    .severity-low,
    .severity-medium,
    .severity-high,
    .severity-critical {
      border-radius: 999px;
      padding: 6px 10px;
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }

    .severity-low {
      background: rgba(16, 185, 129, 0.14);
      color: #a7f3d0;
      border: 1px solid rgba(16, 185, 129, 0.22);
    }

    .severity-medium {
      background: rgba(245, 158, 11, 0.14);
      color: #fde68a;
      border: 1px solid rgba(245, 158, 11, 0.22);
    }

    .severity-high {
      background: rgba(249, 115, 22, 0.14);
      color: #fdba74;
      border: 1px solid rgba(249, 115, 22, 0.22);
    }

    .severity-critical {
      background: rgba(239, 68, 68, 0.14);
      color: #fca5a5;
      border: 1px solid rgba(239, 68, 68, 0.22);
    }

    .risk-category {
      color: var(--muted);
      font-size: 13px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }

    .risk-message {
      color: var(--text);
      font-size: 15px;
      margin-bottom: 10px;
      line-height: 1.5;
    }

    .risk-recommendation {
      color: var(--muted);
      line-height: 1.5;
    }

    .downloads {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      margin-top: 16px;
    }

    .downloads a {
      text-decoration: none;
      color: white;
      background: rgba(79, 140, 255, 0.18);
      border: 1px solid rgba(79, 140, 255, 0.24);
      border-radius: 12px;
      padding: 10px 14px;
      font-size: 14px;
      transition: 0.18s ease;
    }

    .downloads a:hover {
      background: rgba(79, 140, 255, 0.28);
      transform: translateY(-1px);
    }

    .board-card {
      border-radius: 18px;
      padding: 18px;
      margin-top: 14px;
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid rgba(255, 255, 255, 0.08);
    }

    .board-header {
      display: flex;
      justify-content: space-between;
      gap: 14px;
      align-items: center;
      flex-wrap: wrap;
      margin-bottom: 10px;
    }

    .board-title {
      font-size: 18px;
      font-weight: 700;
    }

    .board-rank {
      color: var(--muted);
      font-size: 13px;
      margin-top: 4px;
    }

    .board-score {
      min-width: 110px;
      text-align: center;
      border-radius: 14px;
      padding: 10px 12px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.08);
    }

    .board-score strong {
      display: block;
      font-size: 24px;
      margin-top: 4px;
    }

    .run-card {
      padding: 14px 0;
      border-top: 1px solid rgba(255, 255, 255, 0.08);
    }

    .run-card:first-child {
      border-top: none;
      padding-top: 0;
    }

    .run-name {
      font-weight: 700;
      margin-bottom: 6px;
    }

    .footer-note {
      color: var(--muted);
      font-size: 14px;
      margin-top: 10px;
      line-height: 1.6;
    }

    @media (max-width: 1080px) {
      .grid {
        grid-template-columns: 1fr;
      }
    }

    @media (max-width: 700px) {
      .shell {
        width: min(100% - 18px, 100%);
        margin: 10px auto 24px;
      }

      .hero,
      .card {
        padding: 18px;
      }

      .title-wrap h1 {
        font-size: 30px;
      }

      .form-grid,
      .list-grid {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>
  <div class="shell">
    <section class="hero">
      <div class="hero-top">
        <div class="title-wrap">
          <h1>Silicore</h1>
          <p>
            AI-powered PCB design intelligence for risk detection, explainability,
            revision comparison, and project-level board analysis.
          </p>
        </div>

        <div class="milestone-panel">
          <div class="milestone-label">Current Build</div>
          <div class="milestone-value">14</div>
          <div class="milestone-sub">Modular Service Dashboard</div>
        </div>
      </div>

      <div class="badge-row">
        <div class="badge">Mode: Dashboard</div>
        <div class="badge">Engine: Service Layer</div>
        <div class="badge">Storage: Persistent Runs</div>
        <div class="badge">Exports: JSON / Markdown / HTML</div>
      </div>
    </section>

    {% with messages = get_flashed_messages() %}
      {% if messages %}
        <div class="flash-wrap">
          {% for message in messages %}
            <div class="flash">{{ message }}</div>
          {% endfor %}
        </div>
      {% endif %}
    {% endwith %}

    <div class="grid">
      <div class="left-col">
        <section class="card">
          <h2>Single Board Analysis</h2>
          <p class="section-subtitle">
            Upload one board file for immediate scoring, rule detection, explainability, and export generation.
          </p>

          <form action="{{ url_for('analyze') }}" method="post" enctype="multipart/form-data">
            <div class="form-grid full">
              <div class="field">
                <label>Board File</label>
                <input type="file" name="single_file" required>
              </div>
            </div>

            <div class="button-row">
              <button type="submit" class="primary-btn">Analyze Board</button>
            </div>
          </form>
        </section>

        <section class="card">
          <h2>Project Analysis</h2>
          <p class="section-subtitle">
            Upload multiple board files to rank boards, compare scores, and generate a project-level summary.
          </p>

          <form action="{{ url_for('analyze_project') }}" method="post" enctype="multipart/form-data">
            <div class="form-grid full">
              <div class="field">
                <label>Project Files</label>
                <input type="file" name="project_files" multiple required>
              </div>
            </div>

            <div class="button-row">
              <button type="submit" class="secondary-btn">Analyze Project</button>
            </div>
          </form>
        </section>

        {% if result %}
          <section class="card">
            <div class="result-header">
              <div>
                <h2>Single Board Result</h2>
                <p><strong>File:</strong> {{ result.filename }}</p>
              </div>

              <div class="score-pill">
                <div class="score-label">Risk Score</div>
                <div class="score-value">{{ result.score }} / 10</div>
              </div>
            </div>

            {% if result.board_summary %}
              <div class="metrics">
                <div class="metric">
                  <div class="metric-label">Components</div>
                  <div class="metric-value">{{ result.board_summary.component_count }}</div>
                </div>
                <div class="metric">
                  <div class="metric-label">Nets</div>
                  <div class="metric-value">{{ result.board_summary.net_count }}</div>
                </div>
                <div class="metric">
                  <div class="metric-label">Risk Count</div>
                  <div class="metric-value">{{ result.board_summary.risk_count }}</div>
                </div>
              </div>
            {% endif %}

            {% if result.score_explanation %}
              <div class="list-grid">
                <div class="subpanel">
                  <h3>Score Breakdown</h3>
                  <ul>
                    <li>Start Score: {{ result.score_explanation.start_score }}</li>
                    <li>Total Penalty: {{ result.score_explanation.total_penalty }}</li>
                    <li>Final Score: {{ result.score }}</li>
                  </ul>
                </div>

                <div class="subpanel">
                  <h3>Severity Penalties</h3>
                  {% if result.score_explanation.severity_totals %}
                    <ul>
                      {% for severity, penalty in result.score_explanation.severity_totals.items() %}
                        <li>{{ severity }}: {{ penalty }}</li>
                      {% endfor %}
                    </ul>
                  {% else %}
                    <p>No severity penalties recorded.</p>
                  {% endif %}
                </div>
              </div>

              {% if result.score_explanation.category_totals %}
                <div class="subpanel" style="margin-top: 14px;">
                  <h3>Category Penalties</h3>
                  <ul>
                    {% for category, penalty in result.score_explanation.category_totals.items() %}
                      <li>{{ category }}: {{ penalty }}</li>
                    {% endfor %}
                  </ul>
                </div>
              {% endif %}
            {% endif %}

            <h3>Detailed Findings</h3>
            {% if result.risks %}
              {% for risk in result.risks %}
                <div class="risk-card">
                  <div class="risk-top">
                    <div class="risk-tags">
                      <span class="severity-{{ risk.severity|lower }}">{{ risk.severity }}</span>
                      <span class="tiny-pill">{{ risk.category }}</span>
                      {% if risk.rule_id %}
                        <span class="tiny-pill">{{ risk.rule_id }}</span>
                      {% endif %}
                    </div>
                    <div class="risk-category">Risk Finding</div>
                  </div>

                  <div class="risk-message">{{ risk.message }}</div>
                  <div class="risk-recommendation">
                    <strong>Recommendation:</strong> {{ risk.recommendation }}
                  </div>

                  {% if risk.components %}
                    <div class="pill-row">
                      {% for component in risk.components %}
                        <span class="tiny-pill">{{ component }}</span>
                      {% endfor %}
                    </div>
                  {% endif %}
                </div>
              {% endfor %}
            {% else %}
              <p>No risks detected.</p>
            {% endif %}

            {% if result.downloads %}
              <div class="downloads">
                {% for item in result.downloads %}
                  <a href="{{ item.url }}">{{ item.label }}</a>
                {% endfor %}
              </div>
            {% endif %}
          </section>
        {% endif %}

        {% if project_result %}
          <section class="card">
            <h2>Project Result</h2>

            {% if project_result.project_summary %}
              <div class="metrics">
                <div class="metric">
                  <div class="metric-label">Boards</div>
                  <div class="metric-value">{{ project_result.project_summary.total_boards }}</div>
                </div>
                <div class="metric">
                  <div class="metric-label">Average Score</div>
                  <div class="metric-value">{{ project_result.project_summary.average_score }}</div>
                </div>
                <div class="metric">
                  <div class="metric-label">Best Score</div>
                  <div class="metric-value">{{ project_result.project_summary.best_score }}</div>
                </div>
                <div class="metric">
                  <div class="metric-label">Worst Score</div>
                  <div class="metric-value">{{ project_result.project_summary.worst_score }}</div>
                </div>
              </div>
            {% endif %}

            {% if project_result.boards %}
              {% for board in project_result.boards %}
                <div class="board-card">
                  <div class="board-header">
                    <div>
                      <div class="board-title">#{{ board.rank }} — {{ board.filename }}</div>
                      <div class="board-rank">
                        {% if board.rank == 1 %}Best Board{% endif %}
                        {% if board.rank == project_result.boards|length %}{% if board.rank == 1 %} · {% endif %}Worst Board{% endif %}
                      </div>
                    </div>

                    <div class="board-score">
                      Score
                      <strong>{{ board.score }}</strong>
                    </div>
                  </div>

                  {% if board.score_explanation %}
                    <div class="pill-row">
                      <span class="tiny-pill">Penalty: {{ board.score_explanation.total_penalty }}</span>
                    </div>
                  {% endif %}

                  {% if board.risks %}
                    {% for risk in board.risks %}
                      <div class="risk-card">
                        <div class="risk-top">
                          <div class="risk-tags">
                            <span class="severity-{{ risk.severity|lower }}">{{ risk.severity }}</span>
                            <span class="tiny-pill">{{ risk.category }}</span>
                          </div>
                        </div>

                        <div class="risk-message">{{ risk.message }}</div>
                        <div class="risk-recommendation">
                          <strong>Recommendation:</strong> {{ risk.recommendation }}
                        </div>
                      </div>
                    {% endfor %}
                  {% else %}
                    <p>No risks detected.</p>
                  {% endif %}
                </div>
              {% endfor %}
            {% endif %}

            {% if project_result.downloads %}
              <div class="downloads">
                {% for item in project_result.downloads %}
                  <a href="{{ item.url }}">{{ item.label }}</a>
                {% endfor %}
              </div>
            {% endif %}
          </section>
        {% endif %}
      </div>

      <div class="right-col">
        <section class="card">
          <h2>Config Editor</h2>
          <p class="section-subtitle">
            Tune thresholds and design assumptions without editing config files manually.
          </p>

          <form action="{{ url_for('save_config_route') }}" method="post">
            <h3>Layout</h3>
            <div class="form-grid">
              <div class="field">
                <label>Min Component Spacing</label>
                <input type="text" name="layout_min_component_spacing" value="{{ config.layout.min_component_spacing }}">
              </div>

              <div class="field">
                <label>Density Threshold</label>
                <input type="text" name="layout_density_threshold" value="{{ config.layout.density_threshold }}">
              </div>
            </div>

            <h3>Power</h3>
            <div class="form-grid">
              <div class="field">
                <label>Required Power Nets</label>
                <input type="text" name="power_required_power_nets" value="{{ config.power.required_power_nets }}">
              </div>

              <div class="field">
                <label>Required Ground Nets</label>
                <input type="text" name="power_required_ground_nets" value="{{ config.power.required_ground_nets }}">
              </div>
            </div>

            <h3>Signal</h3>
            <div class="form-grid">
              <div class="field">
                <label>Max Trace Length</label>
                <input type="text" name="signal_max_trace_length" value="{{ config.signal.max_trace_length }}">
              </div>

              <div class="field">
                <label>Critical Nets</label>
                <input type="text" name="signal_critical_nets" value="{{ config.signal.critical_nets }}">
              </div>
            </div>

            <div class="button-row">
              <button type="submit" class="primary-btn">Save Config</button>
            </div>
          </form>
        </section>

        <section class="card">
          <h2>Recent Saved Runs</h2>
          <p class="section-subtitle">
            Review recent dashboard-generated analyses and project exports.
          </p>

          {% if recent_runs %}
            {% for run in recent_runs %}
              <div class="run-card">
                <div class="run-name">{{ run.name }}</div>
                <p>Type: {{ run.run_type }}</p>
                <p>Created: {{ run.created_at }}</p>
              </div>
            {% endfor %}
          {% else %}
            <p>No saved runs yet.</p>
          {% endif %}
        </section>

        <section class="card">
          <h2>Milestone 14 Focus</h2>
          <p class="footer-note">
            Milestone 14 modularizes scoring, report exporting, and project summarization
            so Silicore can keep growing without turning the dashboard and service layer
            into one large, fragile file.
          </p>
        </section>
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
            config_path=CONFIG_PATH,
        )
        return render_dashboard(
            config=service_result["config_view"],
            result=service_result["result"],
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
        return render_dashboard(
            config=service_result["config_view"],
            project_result=service_result["project_result"],
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