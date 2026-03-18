def export_report_markdown(report_text, output_file="report.md"):
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# Silicore Report\n\n")
        f.write("## Generated Output\n\n")
        f.write("```\n")
        f.write(report_text)
        f.write("\n```")


def export_report_html(report_text, output_file="report.html"):
    escaped = (
        report_text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )

    html = f"""
    <html>
    <head>
        <title>Silicore Report</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 40px;
                background: #f7f7f7;
                color: #222;
            }}
            .container {{
                background: white;
                padding: 24px;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            }}
            h1 {{
                margin-top: 0;
            }}
            pre {{
                white-space: pre-wrap;
                word-wrap: break-word;
                font-family: Consolas, monospace;
                font-size: 14px;
                line-height: 1.5;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Silicore Report</h1>
            <pre>{escaped}</pre>
        </div>
    </body>
    </html>
    """

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)