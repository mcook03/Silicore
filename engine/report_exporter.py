from html import escape


def export_markdown_report(report_text, output_path):
    with open(output_path, "w", encoding="utf-8") as file:
        file.write(report_text)


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
  <title>{escape(title)}</title>
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
      border: 1px solid #dbe3ee;
      box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
    }}
    pre {{
      white-space: pre-wrap;
      word-wrap: break-word;
      font-family: inherit;
      margin: 0;
    }}
  </style>
</head>
<body>
  <div class="report">
    <pre>{escaped}</pre>
  </div>
</body>
</html>"""


def export_html_report(report_text, output_path, title="Silicore Report"):
    html = markdown_to_basic_html(report_text, title=title)
    with open(output_path, "w", encoding="utf-8") as file:
        file.write(html)


def export_report_files(report_text, markdown_output_path, html_output_path, title="Silicore Report"):
    export_markdown_report(report_text, markdown_output_path)
    export_html_report(report_text, html_output_path, title=title)


def build_single_board_report(result):
    risks = result.get("risks", [])
    score_explanation = result.get("score_explanation", {})
    board_summary = result.get("board_summary", {})

    lines = [
        "# SILICORE ENGINEERING REPORT",
        "",
        f"- File: {result.get('filename', 'Unknown')}",
        f"- Score: {result.get('score', 0)} / 10",
        "",
        "## Board Overview",
        f"- Component Count: {board_summary.get('component_count', 0)}",
        f"- Net Count: {board_summary.get('net_count', 0)}",
        "",
        "## Score Explanation",
        f"- Start Score: {score_explanation.get('start_score', 10.0)}",
        f"- Total Penalty: {score_explanation.get('total_penalty', 0)}",
        "",
    ]

    severity_totals = score_explanation.get("severity_totals", {})
    if severity_totals:
        lines.append("### Severity Penalties")
        for severity, penalty in severity_totals.items():
            lines.append(f"- {severity}: {penalty}")
        lines.append("")

    category_totals = score_explanation.get("category_totals", {})
    if category_totals:
        lines.append("### Category Penalties")
        for category, penalty in category_totals.items():
            lines.append(f"- {category}: {penalty}")
        lines.append("")

    lines.append("## Detailed Findings")
    lines.append("")

    if risks:
        for index, risk in enumerate(risks, start=1):
            lines.append(f"### {index}. {risk.get('message', 'No message provided')}")
            lines.append(f"- Severity: {risk.get('severity', 'unknown')}")
            lines.append(f"- Category: {risk.get('category', 'uncategorized')}")
            lines.append(f"- Rule: {risk.get('rule_id', 'UNKNOWN_RULE')}")
            lines.append(f"- Recommendation: {risk.get('recommendation', 'No recommendation provided')}")
            if risk.get("components"):
                lines.append(f"- Components: {', '.join(risk['components'])}")
            if risk.get("nets"):
                lines.append(f"- Nets: {', '.join(risk['nets'])}")

            fix_suggestion = risk.get("fix_suggestion")
            if isinstance(fix_suggestion, dict):
                lines.append(f"- Suggested Fix: {fix_suggestion.get('fix', 'No fix provided')}")
                lines.append(f"- Fix Priority: {fix_suggestion.get('priority', 'medium')}")

            lines.append("")
    else:
        lines.append("No risks detected.")

    return "\n".join(lines)


def build_project_report(project_data):
    summary = project_data.get("summary", {})
    boards = project_data.get("boards", [])

    lines = [
        "# SILICORE PROJECT SUMMARY",
        "",
        f"- Total Boards: {summary.get('total_boards', 0)}",
        f"- Average Score: {summary.get('average_score', 0)} / 10",
        f"- Best Score: {summary.get('best_score', 0)} / 10",
        f"- Worst Score: {summary.get('worst_score', 0)} / 10",
        "",
    ]

    severity_counts = summary.get("severity_counts", {})
    if severity_counts:
        lines.append("## Severity Counts")
        for severity, count in severity_counts.items():
            lines.append(f"- {severity}: {count}")
        lines.append("")

    category_counts = summary.get("category_counts", {})
    if category_counts:
        lines.append("## Category Counts")
        for category, count in category_counts.items():
            lines.append(f"- {category}: {count}")
        lines.append("")

    lines.append("## Board Rankings")
    lines.append("")

    for index, board in enumerate(boards, start=1):
        board_summary = board.get("board_summary", {})
        lines.append(f"### #{index} - {board.get('filename', 'Unknown')}")
        lines.append(f"- Score: {board.get('score', 0)} / 10")
        lines.append(f"- Total Risks: {len(board.get('risks', []))}")
        lines.append(f"- Total Penalty: {board.get('score_explanation', {}).get('total_penalty', 0)}")
        lines.append(f"- Component Count: {board_summary.get('component_count', 0)}")
        lines.append(f"- Net Count: {board_summary.get('net_count', 0)}")
        lines.append("")

    return "\n".join(lines)