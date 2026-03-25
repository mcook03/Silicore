import argparse
import json
import os

from engine.config import DEFAULT_CONFIG
from engine.config_loader import load_config
from engine.json_exporter import export_analysis_to_json
from engine.kicad_parser import parse_kicad_file
from engine.normalizer import normalize_pcb
from engine.parser import parse_pcb_file
from engine.project_analyzer import analyze_project_directory
from engine.report_exporter import export_report_files
from engine.report_generator import generate_report
from engine.revision_comparator import compare_revisions
from engine.rule_runner import run_analysis
from engine.visualizer import draw_board


def load_pcb_from_file(filename):
    extension = os.path.splitext(filename)[1].lower()

    if extension == ".kicad_pcb":
        pcb = parse_kicad_file(filename)
    else:
        pcb = parse_pcb_file(filename)

    return normalize_pcb(pcb)


def get_output_directory_for_file(filename):
    base_dir = os.path.dirname(os.path.abspath(filename))
    return base_dir if base_dir else os.getcwd()


def get_output_base_name(filename):
    return os.path.splitext(os.path.basename(filename))[0]


def build_analysis_result(pcb, config=None, debug=False):
    return run_analysis(pcb, config=config, debug=debug)


def analyze_pcb_file(filename, config=None, debug=False):
    pcb = load_pcb_from_file(filename)
    analysis_result = build_analysis_result(pcb, config=config, debug=debug)
    report = generate_report(pcb, analysis_result)

    return pcb, analysis_result, report


def save_single_analysis_outputs(filename, pcb, analysis_result, report):
    output_dir = get_output_directory_for_file(filename)
    output_base = get_output_base_name(filename)

    json_output_path = os.path.join(output_dir, f"{output_base}_analysis.json")
    markdown_output_path = os.path.join(output_dir, f"{output_base}_report.md")
    html_output_path = os.path.join(output_dir, f"{output_base}_report.html")

    export_analysis_to_json(analysis_result, json_output_path)
    export_report_files(report, markdown_output_path, html_output_path)

    return json_output_path, markdown_output_path, html_output_path


def print_single_analysis_summary(filename, analysis_result):
    risk_summary = analysis_result.get("risk_summary", {})
    score_explanation = analysis_result.get("score_explanation", {})

    print()
    print("RESULTS")
    print("========================================")
    print(f"Analyzed: {filename}")
    print(f"Total Risks Found: {risk_summary.get('total_risks', 0)}")
    print(f"Silicore Risk Score: {analysis_result.get('score', 0)} / 10")

    print()
    print("SEVERITY SUMMARY")
    print("========================================")
    by_severity = risk_summary.get("by_severity", {})
    print(f"Low: {by_severity.get('low', 0)}")
    print(f"Medium: {by_severity.get('medium', 0)}")
    print(f"High: {by_severity.get('high', 0)}")
    print(f"Critical: {by_severity.get('critical', 0)}")

    print()
    print("CATEGORY SUMMARY")
    print("========================================")
    by_category = risk_summary.get("by_category", {})
    if by_category:
        for category, count in sorted(by_category.items()):
            print(f"{category}: {count}")
    else:
        print("No category risks found")

    print()
    print("SCORE EXPLAINABILITY")
    print("========================================")
    print(f"Start Score: {score_explanation.get('start_score', 10.0)}")
    print(f"Total Penalty: {score_explanation.get('total_penalty', 0.0)}")
    print(f"Final Score: {score_explanation.get('final_score', analysis_result.get('score', 0))}")

    severity_totals = score_explanation.get("severity_totals", {})
    if severity_totals:
        print()
        print("Penalty by Severity")
        for severity, penalty in sorted(severity_totals.items()):
            print(f"- {severity}: {penalty}")

    category_totals = score_explanation.get("category_totals", {})
    if category_totals:
        print()
        print("Penalty by Category")
        for category, penalty in sorted(category_totals.items()):
            print(f"- {category}: {penalty}")

    detailed_penalties = score_explanation.get("detailed_penalties", [])
    if detailed_penalties:
        print()
        print("DETAILED PENALTIES")
        print("========================================")
        for item in detailed_penalties:
            print(
                f"- {item.get('rule_id', 'UNKNOWN_RULE')} | "
                f"{item.get('severity', 'low')} | "
                f"{item.get('category', 'uncategorized')} | "
                f"Penalty: {item.get('penalty', 0)} | "
                f"{item.get('message', 'No message')}"
            )


def run_single_analysis(filename, config=None, draw=True, debug=False):
    print("Starting Silicore...")
    print("Silicore analysis engine initialized")
    print()
    print("INPUT FILE")
    print("========================================")
    print(f"Analyzing: {filename}")

    pcb, analysis_result, report = analyze_pcb_file(
        filename,
        config=config,
        debug=debug,
    )

    print_single_analysis_summary(filename, analysis_result)

    json_output_path, markdown_output_path, html_output_path = save_single_analysis_outputs(
        filename,
        pcb,
        analysis_result,
        report,
    )

    print()
    print("OUTPUT FILES")
    print("========================================")
    print(f"Saved JSON analysis to: {json_output_path}")
    print(f"Saved Markdown report to: {markdown_output_path}")
    print(f"Saved HTML report to: {html_output_path}")

    if draw:
        print()
        print("Opening board visualization...")
        draw_board(pcb)

    return pcb, analysis_result, report


def run_revision_comparison(old_filename, new_filename, config=None, debug=False):
    print("Starting Silicore...")
    print("Silicore revision comparison initialized")
    print()
    print("REVISION INPUTS")
    print("========================================")
    print(f"Old board: {old_filename}")
    print(f"New board: {new_filename}")

    old_pcb = load_pcb_from_file(old_filename)
    new_pcb = load_pcb_from_file(new_filename)

    old_analysis = build_analysis_result(old_pcb, config=config, debug=debug)
    new_analysis = build_analysis_result(new_pcb, config=config, debug=debug)

    comparison_result = compare_revisions(old_pcb, new_pcb, old_analysis, new_analysis)

    print()
    print("REVISION COMPARISON")
    print("========================================")
    print(f"Old score: {old_analysis.get('score', 0)} / 10")
    print(f"New score: {new_analysis.get('score', 0)} / 10")
    print(f"Score delta: {comparison_result.get('score_delta', 0)}")
    print(f"New risks introduced: {len(comparison_result.get('new_risks', []))}")
    print(f"Resolved risks: {len(comparison_result.get('resolved_risks', []))}")

    output_dir = get_output_directory_for_file(new_filename)
    comparison_output_path = os.path.join(output_dir, "silicore_revision_comparison.json")

    with open(comparison_output_path, "w", encoding="utf-8") as file:
        json.dump(comparison_result, file, indent=4)

    print(f"Saved revision comparison to: {comparison_output_path}")

    return comparison_result


def run_batch_analysis(directory, config=None, draw=False, debug=False):
    print("Starting Silicore...")
    print("Silicore batch analysis initialized")
    print()
    print("PROJECT INPUT")
    print("========================================")
    print(f"Analyzing directory: {directory}")

    project_result = analyze_project_directory(
        directory=directory,
        config=config,
        debug=debug,
        draw=draw,
    )

    summary = project_result.get("summary", {})
    boards = project_result.get("boards", [])

    print()
    print("PROJECT RESULTS")
    print("========================================")
    print(f"Boards analyzed: {summary.get('board_count', len(boards))}")
    print(f"Best board: {summary.get('best_board', 'N/A')}")
    print(f"Worst board: {summary.get('worst_board', 'N/A')}")

    if boards:
        print()
        print("BOARD RANKING")
        print("========================================")
        for board in boards:
            print(
                f"Rank {board.get('rank', '?')}: "
                f"{board.get('board_name', 'Unknown')} | "
                f"Score: {board.get('score', 0)} / 10 | "
                f"Risks: {board.get('risk_summary', {}).get('total_risks', 0)}"
            )

    output_dir = project_result.get(
        "output_directory",
        os.path.join(directory, "silicore_outputs"),
    )

    print()
    print("PROJECT OUTPUTS")
    print("========================================")
    print(f"Output directory: {output_dir}")

    return project_result


def load_active_config(config_path=None):
    config = dict(DEFAULT_CONFIG)

    if config_path:
        loaded_config = load_config(config_path)
        if isinstance(loaded_config, dict):
            config.update(loaded_config)

    return config


def build_argument_parser():
    parser = argparse.ArgumentParser(description="Silicore PCB analysis engine")
    parser.add_argument(
        "--config",
        help="Path to custom JSON config file",
        default=None,
    )

    subparsers = parser.add_subparsers(dest="command")

    analyze_parser = subparsers.add_parser("analyze", help="Analyze a single PCB file")
    analyze_parser.add_argument("file", help="Path to PCB file")
    analyze_parser.add_argument("--no-draw", action="store_true", help="Disable visualization")
    analyze_parser.add_argument("--debug", action="store_true", help="Enable debug output")

    compare_parser = subparsers.add_parser("compare", help="Compare two PCB revisions")
    compare_parser.add_argument("old_file", help="Old PCB file")
    compare_parser.add_argument("new_file", help="New PCB file")
    compare_parser.add_argument("--debug", action="store_true", help="Enable debug output")

    batch_parser = subparsers.add_parser("batch", help="Analyze all supported PCB files in a directory")
    batch_parser.add_argument("directory", help="Directory containing PCB files")
    batch_parser.add_argument("--draw", action="store_true", help="Draw each board during batch analysis")
    batch_parser.add_argument("--debug", action="store_true", help="Enable debug output")

    return parser


def main():
    parser = build_argument_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    config = load_active_config(args.config)

    if args.command == "analyze":
        run_single_analysis(
            args.file,
            config=config,
            draw=not args.no_draw,
            debug=args.debug,
        )
    elif args.command == "compare":
        run_revision_comparison(
            args.old_file,
            args.new_file,
            config=config,
            debug=args.debug,
        )
    elif args.command == "batch":
        run_batch_analysis(
            args.directory,
            config=config,
            draw=args.draw,
            debug=args.debug,
        )


if __name__ == "__main__":
    main()