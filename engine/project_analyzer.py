import json
import os

from engine.json_exporter import export_analysis_to_json
from engine.kicad_parser import parse_kicad_file
from engine.normalizer import normalize_pcb
from engine.parser import parse_pcb_file
from engine.report_exporter import export_report_files
from engine.report_generator import generate_report
from engine.rule_runner import run_analysis
from engine.visualizer import draw_board


SUPPORTED_EXTENSIONS = {".txt", ".kicad_pcb"}


def load_pcb_from_file(filename):
    extension = os.path.splitext(filename)[1].lower()

    if extension == ".kicad_pcb":
        pcb = parse_kicad_file(filename)
    else:
        pcb = parse_pcb_file(filename)

    return normalize_pcb(pcb)


def get_supported_board_files(directory):
    board_files = []

    for entry in sorted(os.listdir(directory)):
        full_path = os.path.join(directory, entry)

        if not os.path.isfile(full_path):
            continue

        extension = os.path.splitext(entry)[1].lower()
        if extension in SUPPORTED_EXTENSIONS:
            board_files.append(full_path)

    return board_files


def build_project_summary_markdown(board_results):
    lines = []
    lines.append("# SILICORE PROJECT SUMMARY")
    lines.append("")

    lines.append(f"- Board Count: {len(board_results)}")
    lines.append("")

    if board_results:
        lines.append(f"- Best Board: {board_results[0]['board_name']}")
        lines.append(f"- Worst Board: {board_results[-1]['board_name']}")
    else:
        lines.append("- Best Board: N/A")
        lines.append("- Worst Board: N/A")

    lines.append("")

    for board in board_results:
        lines.append(f"## Rank {board['rank']} — {board['board_name']}")
        lines.append(f"- Score: {board['score']} / 10")
        lines.append(f"- Total Risks: {board['risk_summary'].get('total_risks', 0)}")
        lines.append("")

        by_severity = board["risk_summary"].get("by_severity", {})
        lines.append("### Severity Summary")
        lines.append(f"- Low: {by_severity.get('low', 0)}")
        lines.append(f"- Medium: {by_severity.get('medium', 0)}")
        lines.append(f"- High: {by_severity.get('high', 0)}")
        lines.append(f"- Critical: {by_severity.get('critical', 0)}")
        lines.append("")

        by_category = board["risk_summary"].get("by_category", {})
        lines.append("### Category Summary")
        if by_category:
            for category, count in sorted(by_category.items()):
                lines.append(f"- {category}: {count}")
        else:
            lines.append("- No category risks found")
        lines.append("")

        score_explanation = board.get("score_explanation", {})
        lines.append("### Score Explainability")
        lines.append(f"- Start Score: {score_explanation.get('start_score', 10.0)}")
        lines.append(f"- Total Penalty: {score_explanation.get('total_penalty', 0.0)}")
        lines.append(f"- Final Score: {score_explanation.get('final_score', board['score'])}")
        lines.append("")

    return "\n".join(lines)


def analyze_project_directory(directory, config=None, debug=False, draw=False):
    board_files = get_supported_board_files(directory)
    output_directory = os.path.join(directory, "silicore_outputs")
    os.makedirs(output_directory, exist_ok=True)

    board_results = []

    for file_path in board_files:
        pcb = load_pcb_from_file(file_path)
        analysis_result = run_analysis(pcb, config=config, debug=debug)
        report = generate_report(pcb, analysis_result)

        board_name = os.path.basename(file_path)
        board_base = os.path.splitext(board_name)[0]

        json_output_path = os.path.join(output_directory, f"{board_base}_analysis.json")
        markdown_output_path = os.path.join(output_directory, f"{board_base}_report.md")
        html_output_path = os.path.join(output_directory, f"{board_base}_report.html")

        export_analysis_to_json(analysis_result, json_output_path)
        export_report_files(report, markdown_output_path, html_output_path)

        if draw:
            draw_board(pcb)

        board_results.append({
            "board_name": board_name,
            "file_path": file_path,
            "score": analysis_result.get("score", 0),
            "risks": analysis_result.get("risks", []),
            "risk_summary": analysis_result.get("risk_summary", {}),
            "score_explanation": analysis_result.get("score_explanation", {}),
            "outputs": {
                "json": json_output_path,
                "markdown": markdown_output_path,
                "html": html_output_path,
            },
        })

    board_results.sort(key=lambda item: item["score"], reverse=True)

    for index, board in enumerate(board_results, start=1):
        board["rank"] = index

    summary = {
        "board_count": len(board_results),
        "best_board": board_results[0]["board_name"] if board_results else None,
        "worst_board": board_results[-1]["board_name"] if board_results else None,
    }

    project_summary = {
        "summary": summary,
        "boards": board_results,
    }

    project_summary_json_path = os.path.join(output_directory, "silicore_project_summary.json")
    project_summary_markdown_path = os.path.join(output_directory, "silicore_project_summary.md")
    project_summary_html_path = os.path.join(output_directory, "silicore_project_summary.html")

    with open(project_summary_json_path, "w", encoding="utf-8") as file:
        json.dump(project_summary, file, indent=4)

    markdown_text = build_project_summary_markdown(board_results)

    with open(project_summary_markdown_path, "w", encoding="utf-8") as file:
        file.write(markdown_text)

    html_text = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Silicore Project Summary</title>
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
        <pre>{markdown_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")}</pre>
    </div>
</body>
</html>
"""

    with open(project_summary_html_path, "w", encoding="utf-8") as file:
        file.write(html_text)

    return {
        "summary": summary,
        "boards": board_results,
        "output_directory": output_directory,
        "project_summary_files": {
            "json": project_summary_json_path,
            "markdown": project_summary_markdown_path,
            "html": project_summary_html_path,
        },
    }