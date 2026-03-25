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


def export_markdown_report(report_text, output_path):
    with open(output_path, "w", encoding="utf-8") as file:
        file.write(report_text)


def export_html_report(report_text, output_path, title="Silicore Report"):
    html = markdown_to_basic_html(report_text, title=title)

    with open(output_path, "w", encoding="utf-8") as file:
        file.write(html)


def export_report_files(report_text, markdown_output_path, html_output_path, title="Silicore Report"):
    export_markdown_report(report_text, markdown_output_path)
    export_html_report(report_text, html_output_path, title=title)