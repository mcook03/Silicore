import argparse
import os

from engine.parser import start_engine, parse_pcb_file
from engine.kicad_parser import parse_kicad_file
from engine.rule_runner import run_analysis
from engine.visualizer import draw_board
from engine.report_generator import generate_report
from engine.report_exporter import export_report_markdown, export_report_html
from engine.json_exporter import export_analysis_to_json
from engine.revision_comparator import compare_revisions
from engine.normalizer import normalize_pcb
from engine.config_loader import load_config
from engine.project_analyzer import (
    discover_pcb_files,
    summarize_project,
    generate_project_summary_report,
    export_project_summary_json,
    make_project_output_paths,
)


def load_pcb(filename):
    if filename.endswith(".kicad_pcb"):
        pcb = parse_kicad_file(filename)
    else:
        pcb = parse_pcb_file(filename)

    pcb = normalize_pcb(pcb)
    return pcb


def print_debug_risks(risks):
    print("\nRAW RISKS DEBUG")
    print("=" * 40)
    for risk in risks:
        print(risk)

    print("\nPOWER RAIL + RETURN PATH METRICS CHECK")
    print("=" * 40)

    found = False
    for risk in risks:
        if risk["rule_id"] in {"power_rail", "return_path"}:
            found = True
            print(f"Rule: {risk['rule_id']}")
            print(f"Message: {risk['message']}")
            print(f"Metrics: {risk.get('metrics')}")
            print("-" * 40)

    if not found:
        print("No power_rail or return_path risks found.")


def make_output_name(filename, suffix, extension):
    base = os.path.splitext(os.path.basename(filename))[0]
    return f"{base}_{suffix}.{extension}"


def make_output_path(directory, filename, suffix, extension):
    base = os.path.splitext(os.path.basename(filename))[0]
    return os.path.join(directory, f"{base}_{suffix}.{extension}")


def analyze_pcb_file(filename, config, debug=False):
    pcb = load_pcb(filename)
    risks, score = run_analysis(pcb, config=config)

    if debug:
        print_debug_risks(risks)

    report = generate_report(pcb, risks, score)
    return pcb, risks, score, report


def export_single_board_outputs(filename, output_directory, pcb, risks, score, report):
    json_file = make_output_path(output_directory, filename, "analysis", "json")
    md_file = make_output_path(output_directory, filename, "report", "md")
    html_file = make_output_path(output_directory, filename, "report", "html")

    export_analysis_to_json(pcb, risks, score, json_file)
    export_report_markdown(report, md_file)
    export_report_html(report, html_file)

    return json_file, md_file, html_file


def run_single_analysis(filename, config, draw=True, debug=False):
    print("\nINPUT FILE")
    print("=" * 40)
    print(f"Analyzing: {filename}")

    pcb, risks, score, report = analyze_pcb_file(filename, config=config, debug=debug)
    print(report)

    json_file = make_output_name(filename, "analysis", "json")
    md_file = make_output_name(filename, "report", "md")
    html_file = make_output_name(filename, "report", "html")

    export_analysis_to_json(pcb, risks, score, json_file)
    export_report_markdown(report, md_file)
    export_report_html(report, html_file)

    print(f"\nJSON exported to: {json_file}")
    print(f"Markdown report exported to: {md_file}")
    print(f"HTML report exported to: {html_file}")

    if draw:
        draw_board(pcb, risks)


def run_revision_comparison(old_filename, new_filename, config, draw=True, debug=False):
    print("\nREVISION INPUTS")
    print("=" * 40)
    print(f"Old file: {old_filename}")
    print(f"New file: {new_filename}")

    pcb_old = load_pcb(old_filename)
    pcb_new = load_pcb(new_filename)

    old_risks, old_score = run_analysis(pcb_old, config=config)
    new_risks, new_score = run_analysis(pcb_new, config=config)

    if debug:
        print_debug_risks(new_risks)

    report = generate_report(pcb_new, new_risks, new_score)
    comparison = compare_revisions(old_risks, new_risks, old_score, new_score)

    print(report)
    print()
    print(comparison)

    json_file = make_output_name(new_filename, "analysis", "json")
    md_file = make_output_name(new_filename, "report", "md")
    html_file = make_output_name(new_filename, "report", "html")

    export_analysis_to_json(pcb_new, new_risks, new_score, json_file)
    export_report_markdown(report + "\n\n" + comparison, md_file)
    export_report_html(report + "\n\n" + comparison, html_file)

    print(f"\nJSON exported to: {json_file}")
    print(f"Markdown report exported to: {md_file}")
    print(f"HTML report exported to: {html_file}")

    if draw:
        draw_board(pcb_new, new_risks)


def run_batch_analysis(directory, config, draw=False, debug=False):
    print("\nBATCH INPUT")
    print("=" * 40)
    print(f"Scanning directory: {directory}")

    file_paths = discover_pcb_files(directory)

    if not file_paths:
        print("No supported PCB files found.")
        print("Supported extensions: .kicad_pcb, .txt")
        return

    print(f"Found {len(file_paths)} supported PCB file(s).")

    output_directory = os.path.join(directory, "silicore_outputs")
    os.makedirs(output_directory, exist_ok=True)

    board_results = []

    for index, file_path in enumerate(file_paths, start=1):
        print()
        print(f"[{index}/{len(file_paths)}] Analyzing: {file_path}")

        try:
            pcb, risks, score, report = analyze_pcb_file(file_path, config=config, debug=debug)
            json_file, md_file, html_file = export_single_board_outputs(
                file_path,
                output_directory,
                pcb,
                risks,
                score,
                report,
            )

            board_results.append(
                {
                    "file_path": file_path,
                    "board_name": os.path.basename(file_path),
                    "component_count": len(pcb.components),
                    "net_count": len(pcb.nets),
                    "risk_count": len(risks),
                    "score": score,
                    "category_counts": _count_categories(risks),
                    "severity_counts": _count_severities(risks),
                    "risks": risks,
                }
            )

            print(f"Score: {score} / 10")
            print(f"Risks: {len(risks)}")
            print(f"JSON exported to: {json_file}")
            print(f"Markdown report exported to: {md_file}")
            print(f"HTML report exported to: {html_file}")

            if draw:
                draw_board(pcb, risks)

        except Exception as e:
            print(f"Analysis failed for {file_path}: {e}")

    if not board_results:
        print("\nNo boards were successfully analyzed.")
        return

    summary = summarize_project(board_results)
    summary_report = generate_project_summary_report(board_results, summary)
    summary_paths = make_project_output_paths(output_directory)

    export_project_summary_json(summary_paths["json"], board_results, summary)
    export_report_markdown(summary_report, summary_paths["md"])
    export_report_html(summary_report, summary_paths["html"])

    print("\nPROJECT SUMMARY")
    print("=" * 40)
    print(summary_report)
    print()
    print(f"Project summary JSON exported to: {summary_paths['json']}")
    print(f"Project summary Markdown exported to: {summary_paths['md']}")
    print(f"Project summary HTML exported to: {summary_paths['html']}")


def _count_categories(risks):
    counts = {}
    for risk in risks:
        category = risk.get("category", "other")
        counts[category] = counts.get(category, 0) + 1
    return counts


def _count_severities(risks):
    counts = {}
    for risk in risks:
        severity = risk.get("severity", "unknown")
        counts[severity] = counts.get(severity, 0) + 1
    return counts


def build_parser():
    parser = argparse.ArgumentParser(
        prog="Silicore",
        description="AI-powered hardware design intelligence tool",
    )
    parser.add_argument("--config", help="Path to a JSON config file", default=None)

    subparsers = parser.add_subparsers(dest="command")

    analyze_parser = subparsers.add_parser("analyze", help="Analyze a single PCB file")
    analyze_parser.add_argument("file")
    analyze_parser.add_argument("--debug", action="store_true")
    analyze_parser.add_argument("--no-draw", action="store_true")

    compare_parser = subparsers.add_parser("compare", help="Compare two PCB revisions")
    compare_parser.add_argument("old_file")
    compare_parser.add_argument("new_file")
    compare_parser.add_argument("--debug", action="store_true")
    compare_parser.add_argument("--no-draw", action="store_true")

    batch_parser = subparsers.add_parser("batch", help="Analyze all supported PCB files in a directory")
    batch_parser.add_argument("directory")
    batch_parser.add_argument("--debug", action="store_true")
    batch_parser.add_argument("--draw", action="store_true")

    return parser


def main():
    print("Starting Silicore...")
    start_engine()

    parser = build_parser()
    args = parser.parse_args()

    try:
        config = load_config(args.config)
    except Exception as e:
        print(f"Failed to load config: {e}")
        return

    if args.command == "analyze":
        run_single_analysis(args.file, config=config, draw=not args.no_draw, debug=args.debug)
    elif args.command == "compare":
        run_revision_comparison(args.old_file, args.new_file, config=config, draw=not args.no_draw, debug=args.debug)
    elif args.command == "batch":
        run_batch_analysis(args.directory, config=config, draw=args.draw, debug=args.debug)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()