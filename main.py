import os
import sys

from engine.config_loader import load_config
from engine.services.analysis_service import (
    analyze_project_directory,
    run_single_analysis_from_path,
)


def print_single_result(result):
    print("\nSILICORE ENGINEERING REPORT")
    print("-" * 40)
    print(f"File: {result['filename']}")
    print(f"Silicore Risk Score: {result['score']} / 10")
    print(f"Total Risks: {len(result['risks'])}")
    print(f"Total Penalty: {result['score_explanation'].get('total_penalty', 0)}")

    severity_totals = result["score_explanation"].get("severity_totals", {})
    if severity_totals:
        print("\nSeverity Penalties:")
        for severity, value in severity_totals.items():
            print(f"  {severity}: {value}")

    category_totals = result["score_explanation"].get("category_totals", {})
    if category_totals:
        print("\nCategory Penalties:")
        for category, value in category_totals.items():
            print(f"  {category}: {value}")

    print("\nDetailed Findings:")
    if result["risks"]:
        for risk in result["risks"]:
            print(
                f"  [{str(risk.get('severity', 'low')).upper()}] "
                f"{risk.get('category', 'unknown')}: "
                f"{risk.get('message', 'No message')}"
            )
            print(f"    Recommendation: {risk.get('recommendation', 'Review this finding.')}")
    else:
        print("  No risks detected.")

    if result.get("json_path"):
        print(f"\nJSON: {result['json_path']}")
    if result.get("report_md_path"):
        print(f"Markdown: {result['report_md_path']}")
    if result.get("report_html_path"):
        print(f"HTML: {result['report_html_path']}")


def print_project_result(result):
    summary = result["summary"]
    boards = result["boards"]

    print("\nSILICORE PROJECT SUMMARY")
    print("-" * 40)
    print(f"Total Boards: {summary['total_boards']}")
    print(f"Average Score: {summary['average_score']} / 10")
    print(f"Best Score: {summary['best_score']} / 10")
    print(f"Worst Score: {summary['worst_score']} / 10")

    print("\nBoard Rankings:")
    for index, board in enumerate(boards, start=1):
        print(f"  #{index} {board['filename']} — {board['score']} / 10")

    if result.get("summary_json_path"):
        print(f"\nJSON: {result['summary_json_path']}")
    if result.get("summary_md_path"):
        print(f"Markdown: {result['summary_md_path']}")
    if result.get("summary_html_path"):
        print(f"HTML: {result['summary_html_path']}")


def run_analysis(file_path, config=None):
    if config is None:
        config = load_config("custom_config.json")

    output_dir = os.path.dirname(file_path) or "."
    return run_single_analysis_from_path(
        file_path=file_path,
        config=config,
        output_dir=output_dir
    )


def main():
    config = load_config("custom_config.json")

    if len(sys.argv) < 3:
        print("Usage:")
        print("  python3 main.py analyze <pcb_file>")
        print("  python3 main.py batch <directory>")
        sys.exit(1)

    command = sys.argv[1]

    if command == "analyze":
        file_path = sys.argv[2]
        result = run_analysis(file_path, config=config)
        print_single_result(result)
        return

    if command == "batch":
        directory_path = sys.argv[2]
        result = analyze_project_directory(directory_path, config=config)
        print_project_result(result)
        return

    print(f"Unknown command: {command}")
    sys.exit(1)


if __name__ == "__main__":
    main()