import os
import tempfile

from flask import Flask, request, render_template_string

from engine.parser import start_engine, parse_pcb_file
from engine.kicad_parser import parse_kicad_file
from engine.normalizer import normalize_pcb
from engine.rule_runner import run_analysis
from engine.report_generator import generate_report
from engine.config_loader import load_config

app = Flask(__name__)
start_engine()

HTML = """
<!doctype html>
<html>
<head>
    <title>Silicore Local Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f7fa; }
        .card { background: white; padding: 24px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.08); max-width: 1000px; margin: auto; }
        h1 { margin-top: 0; }
        pre { width: 100%; white-space: pre-wrap; }
        input[type=file] { margin-bottom: 16px; }
        .score { font-size: 20px; font-weight: bold; margin-bottom: 16px; }
        .risk { border-bottom: 1px solid #ddd; padding: 10px 0; }
        .sev-high { color: #b00020; }
        .sev-medium { color: #a15c00; }
        .sev-low { color: #00695c; }
        .sev-critical { color: #7b0000; font-weight: bold; }
        .error { color: #b00020; font-weight: bold; margin-top: 16px; }
    </style>
</head>
<body>
    <div class="card">
        <h1>Silicore Local Dashboard</h1>
        <form method="post" enctype="multipart/form-data">
            <input type="file" name="pcb_file" required>
            <button type="submit">Analyze</button>
        </form>

        {% if error %}
            <div class="error">{{ error }}</div>
        {% endif %}

        {% if report %}
            <div class="score">Risk Score: {{ score }} / 10</div>

            <h2>Report</h2>
            <pre>{{ report }}</pre>

            <h2>Risks</h2>
            {% for risk in risks %}
                <div class="risk">
                    <div class="sev-{{ risk.severity }}">[{{ risk.severity.upper() }}] {{ risk.message }}</div>
                    <div><strong>Category:</strong> {{ risk.category }}</div>
                    <div><strong>Recommendation:</strong> {{ risk.recommendation }}</div>
                    <div><strong>Confidence:</strong> {{ risk.confidence }}</div>
                </div>
            {% endfor %}
        {% endif %}
    </div>
</body>
</html>
"""

CONFIG = load_config()


def load_pcb(filename):
    if filename.endswith(".kicad_pcb"):
        pcb = parse_kicad_file(filename)
    else:
        pcb = parse_pcb_file(filename)

    pcb = normalize_pcb(pcb)
    return pcb


@app.route("/", methods=["GET", "POST"])
def home():
    report = None
    risks = []
    score = None
    error = None

    if request.method == "POST":
        uploaded = request.files.get("pcb_file")

        if not uploaded or not uploaded.filename:
            error = "Please upload a PCB file."
        else:
            suffix = os.path.splitext(uploaded.filename)[1]
            temp_path = None

            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    uploaded.save(tmp.name)
                    temp_path = tmp.name

                pcb = load_pcb(temp_path)
                risks, score = run_analysis(pcb, config=CONFIG)
                report = generate_report(pcb, risks, score)

            except Exception as e:
                error = f"Analysis failed: {e}"

            finally:
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)

    return render_template_string(
        HTML,
        report=report,
        risks=risks,
        score=score,
        error=error,
    )


if __name__ == "__main__":
    app.run(debug=True)