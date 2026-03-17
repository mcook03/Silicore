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


def run_single_analysis(filename, config, draw=True, debug=False):
    print("\nINPUT FILE")
    print("=" * 40)
    print(f"Analyzing: {filename}")

    pcb = load_pcb(filename)
    risks, score = run_analysis(pcb, config=config)

    if debug:
        print_debug_risks(risks)

    report = generate_report(pcb, risks, score)
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


def build_parser():
    parser = argparse.ArgumentParser(prog="Silicore", description="AI-powered hardware design intelligence tool")
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
    else:
        parser.print_help()


if __name__ == "__main__":
    main()