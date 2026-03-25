import json
import os
from datetime import datetime
from html import escape


SUPPORTED_EXTENSIONS = {".txt", ".kicad_pcb"}


def _safe_filename(filename):
    return filename.replace("/", "_").replace("\\", "_").strip()


def _build_project_summary(boards):
    if not boards:
        return {
            "total_boards": 0,
            "average_score": 0,
            "best_score": 0,
            "worst_score": 0,
            "severity_counts": {},
            "category_counts": {}
        }

    total_score = sum(board.get("score", 0) for board in boards)
    average_score = round(total_score / len(boards), 2)
    best_score = max(board.get("score", 0) for board in boards)
    worst_score = min(board.get("score", 0) for board in boards)

    severity_counts = {}
    category_counts = {}

    for board in boards:
        for risk in board.get("risks", []):
            severity = risk.get("severity", "unknown")
            category = risk.get("category", "unknown")

            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            category_counts[category] = category_counts.get(category, 0) + 1

    return {
        "total_boards": len(boards),
        "average_score": average_score,
        "best_score": best_score,
        "worst_score": worst_score,
        "severity_counts": severity_counts,
        "category_counts": category_counts
    }


def _write_json(path, data):
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


def _write_markdown(path, project_data):
    summary = project_data["summary"]
    boards = project_data["boards"]

    lines = [
        "# SILICORE PROJECT SUMMARY",
        "",
        f"- Total Boards: {summary['total_boards']}",
        f"- Average Score: {summary['average_score']} / 10",
        f"- Best Score: {summary['best_score']} / 10",
        f"- Worst Score: {summary['worst_score']} / 10",
        "",
        "## Severity Summary",
        ""
    ]

    if summary["severity_counts"]:
        for severity, count in summary["severity_counts"].items():
            lines.append(f"- {severity}: {count}")
    else:
        lines.append("- No risks detected")

    lines.extend([
        "",
        "## Category Summary",
        ""
    ])

    if summary["category_counts"]:
        for category, count in summary["category_counts"].items():
            lines.append(f"- {category}: {count}")
    else:
        lines.append("- No risks detected")

    lines.extend([
        "",
        "## Board Rankings",
        ""
    ])

    for index, board in enumerate(boards, start=1):
        lines.append(f"### #{index} {board['filename']}")
        lines.append(f"- Score: {board['score']} / 10")
        lines.append(f"- Total Risks: {len(board.get('risks', []))}")

        if board.get("score_explanation"):
            lines.append(
                f"- Total Penalty: {board['score_explanation'].get('total_penalty', 0)}"
            )

        if board.get("risks"):
            lines.append("")
            lines.append("#### Findings")
            lines.append("")

            for risk in board["risks"]:
                lines.append(
                    f"- [{risk.get('severity', 'unknown').upper()}] "
                    f"{risk.get('category', 'unknown')}: "
                    f"{risk.get('message', 'No message')}"
                )
                lines.append(
                    f"  - Recommendation: {risk.get('recommendation', 'No recommendation')}"
                )
        else:
            lines.append("- No risks detected")

        lines.append("")

    with open(path, "w", encoding="utf-8") as file:
        file.write("\n".join(lines))


def _write_html(path, project_data):
    summary = project_data["summary"]
    boards = project_data["boards"]

    severity_html = ""
    if summary["severity_counts"]:
        for severity, count in summary["severity_counts"].items():
            severity_html += f"<li>{escape(str(severity))}: {count}</li>"
    else:
        severity_html = "<li>No risks detected</li>"

    category_html = ""
    if summary["category_counts"]:
        for category, count in summary["category_counts"].items():
            category_html += f"<li>{escape(str(category))}: {count}</li>"
    else:
        category_html = "<li>No risks detected</li>"

    boards_html = ""
    for index, board in enumerate(boards, start=1):
        risks_html = ""

        if board.get("risks"):
            for risk in board["risks"]:
                risks_html += f"""
                <div class="risk">
                    <p><strong>Severity:</strong> {escape(str(risk.get('severity', 'unknown')))}</p>
                    <p><strong>Category:</strong> {escape(str(risk.get('category', 'unknown')))}</p>
                    <p><strong>Message:</strong> {escape(str(risk.get('message', 'No message')))}</p>
                    <p><strong>Recommendation:</strong> {escape(str(risk.get('recommendation', 'No recommendation')))}</p>
                </div>
                """
        else:
            risks_html = "<p>No risks detected.</p>"

        total_penalty = 0
        if board.get("score_explanation"):
            total_penalty = board["score_explanation"].get("total_penalty", 0)

        boards_html += f"""
        <div class="board">
            <h2>#{index} {escape(str(board['filename']))}</h2>
            <p><strong>Score:</strong> {board['score']} / 10</p>
            <p><strong>Total Risks:</strong> {len(board.get('risks', []))}</p>
            <p><strong>Total Penalty:</strong> {total_penalty}</p>
            {risks_html}
        </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Silicore Project Summary</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 32px;
                background: #f8fafc;
                color: #0f172a;
            }}
            .card {{
                background: white;
                border: 1px solid #cbd5e1;
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 20px;
            }}
            .board {{
                background: white;
                border: 1px solid #cbd5e1;
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 20px;
            }}
            .risk {{
                margin-top: 12px;
                padding-top: 12px;
                border-top: 1px solid #e2e8f0;
            }}
        </style>
    </head>
    <body>
        <h1>Silicore Project Summary</h1>

        <div class="card">
            <p><strong>Total Boards:</strong> {summary['total_boards']}</p>
            <p><strong>Average Score:</strong> {summary['average_score']} / 10</p>
            <p><strong>Best Score:</strong> {summary['best_score']} / 10</p>
            <p><strong>Worst Score:</strong> {summary['worst_score']} / 10</p>

            <h3>Severity Summary</h3>
            <ul>{severity_html}</ul>

            <h3>Category Summary</h3>
            <ul>{category_html}</ul>
        </div>

        {boards_html}
    </body>
    </html>
    """

    with open(path, "w", encoding="utf-8") as file:
        file.write(html)


def run_project_analysis(file_paths, config=None):
    from main import run_analysis

    boards = []

    for file_path in file_paths:
        analysis_result = run_analysis(file_path, config=config)

        boards.append({
            "filename": os.path.basename(file_path),
            "score": analysis_result.get("score", 0),
            "risks": analysis_result.get("risks", []),
            "score_explanation": analysis_result.get("score_explanation", {}),
            "source_file": file_path
        })

    boards.sort(key=lambda board: board.get("score", 0), reverse=True)

    summary = _build_project_summary(boards)

    output_dir = os.path.dirname(file_paths[0]) if file_paths else "."
    summary_json_path = os.path.join(output_dir, "silicore_project_summary.json")
    summary_md_path = os.path.join(output_dir, "silicore_project_summary.md")
    summary_html_path = os.path.join(output_dir, "silicore_project_summary.html")

    project_data = {
        "generated_at": datetime.now().isoformat(),
        "summary": summary,
        "boards": boards
    }

    _write_json(summary_json_path, project_data)
    _write_markdown(summary_md_path, project_data)
    _write_html(summary_html_path, project_data)

    return {
        "boards": boards,
        "summary": summary,
        "summary_json_path": summary_json_path,
        "summary_md_path": summary_md_path,
        "summary_html_path": summary_html_path
    }


def analyze_project_directory(directory_path, config=None):
    if not os.path.isdir(directory_path):
        raise FileNotFoundError(f"Directory not found: {directory_path}")

    file_paths = []

    for name in sorted(os.listdir(directory_path)):
        full_path = os.path.join(directory_path, name)

        if not os.path.isfile(full_path):
            continue

        extension = os.path.splitext(name)[1].lower()
        if extension in SUPPORTED_EXTENSIONS:
            file_paths.append(full_path)

    if not file_paths:
        return {
            "boards": [],
            "summary": _build_project_summary([]),
            "summary_json_path": None,
            "summary_md_path": None,
            "summary_html_path": None
        }

    return run_project_analysis(file_paths, config=config)