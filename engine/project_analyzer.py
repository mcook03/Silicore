import os
import json
from collections import Counter


SUPPORTED_EXTENSIONS = {".kicad_pcb", ".txt"}


def discover_pcb_files(directory):
    pcb_files = []

    for root, _, files in os.walk(directory):
        for filename in files:
            extension = os.path.splitext(filename)[1].lower()
            if extension in SUPPORTED_EXTENSIONS:
                pcb_files.append(os.path.join(root, filename))

    pcb_files.sort()
    return pcb_files


def build_board_result(file_path, pcb, risks, score):
    category_counter = Counter()
    severity_counter = Counter()

    for risk in risks:
        category_counter[risk.get("category", "other")] += 1
        severity_counter[risk.get("severity", "unknown")] += 1

    return {
        "file_path": file_path,
        "board_name": os.path.basename(file_path),
        "component_count": len(pcb.components),
        "net_count": len(pcb.nets),
        "risk_count": len(risks),
        "score": score,
        "category_counts": dict(category_counter),
        "severity_counts": dict(severity_counter),
        "risks": risks,
    }


def analyze_project(file_paths, config, analyze_file_func):
    results = []

    for file_path in file_paths:
        pcb, risks, score, _ = analyze_file_func(file_path, config=config, debug=False)
        result = build_board_result(file_path, pcb, risks, score)
        results.append(result)

    return results


def summarize_project(results):
    total_boards = len(results)

    if total_boards == 0:
        return {
            "boards_analyzed": 0,
            "average_score": 0.0,
            "best_board": None,
            "worst_board": None,
            "total_components": 0,
            "total_nets": 0,
            "total_risks": 0,
            "risk_categories": {},
            "risk_severities": {},
            "boards_below_threshold_5": [],
        }

    total_components = sum(result["component_count"] for result in results)
    total_nets = sum(result["net_count"] for result in results)
    total_risks = sum(result["risk_count"] for result in results)
    average_score = round(sum(result["score"] for result in results) / total_boards, 2)

    best_board = max(results, key=lambda item: item["score"])
    worst_board = min(results, key=lambda item: item["score"])

    category_counter = Counter()
    severity_counter = Counter()

    for result in results:
        category_counter.update(result["category_counts"])
        severity_counter.update(result["severity_counts"])

    boards_below_threshold_5 = [
        {
            "board_name": result["board_name"],
            "score": result["score"],
            "risk_count": result["risk_count"],
        }
        for result in results
        if result["score"] < 5.0
    ]

    boards_below_threshold_5.sort(key=lambda item: item["score"])

    return {
        "boards_analyzed": total_boards,
        "average_score": average_score,
        "best_board": {
            "board_name": best_board["board_name"],
            "score": best_board["score"],
            "risk_count": best_board["risk_count"],
        },
        "worst_board": {
            "board_name": worst_board["board_name"],
            "score": worst_board["score"],
            "risk_count": worst_board["risk_count"],
        },
        "total_components": total_components,
        "total_nets": total_nets,
        "total_risks": total_risks,
        "risk_categories": dict(category_counter),
        "risk_severities": dict(severity_counter),
        "boards_below_threshold_5": boards_below_threshold_5,
    }


def generate_project_summary_report(results, summary):
    lines = []

    lines.append("SILICORE PROJECT SUMMARY")
    lines.append("=" * 60)
    lines.append(f"Boards analyzed: {summary['boards_analyzed']}")
    lines.append(f"Average score: {summary['average_score']} / 10")
    lines.append(f"Total components: {summary['total_components']}")
    lines.append(f"Total nets: {summary['total_nets']}")
    lines.append(f"Total risks: {summary['total_risks']}")
    lines.append("")

    if summary["best_board"]:
        lines.append("BEST BOARD")
        lines.append("-" * 60)
        lines.append(
            f"{summary['best_board']['board_name']} | "
            f"Score: {summary['best_board']['score']} | "
            f"Risks: {summary['best_board']['risk_count']}"
        )
        lines.append("")

    if summary["worst_board"]:
        lines.append("WORST BOARD")
        lines.append("-" * 60)
        lines.append(
            f"{summary['worst_board']['board_name']} | "
            f"Score: {summary['worst_board']['score']} | "
            f"Risks: {summary['worst_board']['risk_count']}"
        )
        lines.append("")

    lines.append("RISK CATEGORIES")
    lines.append("-" * 60)
    if summary["risk_categories"]:
        sorted_categories = sorted(
            summary["risk_categories"].items(),
            key=lambda item: item[1],
            reverse=True,
        )
        for category, count in sorted_categories:
            lines.append(f"{category}: {count}")
    else:
        lines.append("No categories found.")
    lines.append("")

    lines.append("RISK SEVERITIES")
    lines.append("-" * 60)
    if summary["risk_severities"]:
        severity_order = ["critical", "high", "medium", "low", "unknown"]
        sorted_severities = sorted(
            summary["risk_severities"].items(),
            key=lambda item: severity_order.index(item[0]) if item[0] in severity_order else 99,
        )
        for severity, count in sorted_severities:
            lines.append(f"{severity}: {count}")
    else:
        lines.append("No severities found.")
    lines.append("")

    lines.append("LOW-SCORING BOARDS (SCORE < 5.0)")
    lines.append("-" * 60)
    if summary["boards_below_threshold_5"]:
        for board in summary["boards_below_threshold_5"]:
            lines.append(
                f"{board['board_name']} | Score: {board['score']} | Risks: {board['risk_count']}"
            )
    else:
        lines.append("None")
    lines.append("")

    lines.append("PER-BOARD RESULTS")
    lines.append("-" * 60)
    sorted_results = sorted(results, key=lambda item: item["score"])
    for result in sorted_results:
        lines.append(
            f"{result['board_name']} | "
            f"Score: {result['score']} | "
            f"Risks: {result['risk_count']} | "
            f"Components: {result['component_count']} | "
            f"Nets: {result['net_count']}"
        )

    return "\n".join(lines)


def export_project_summary_json(output_path, results, summary):
    payload = {
        "summary": summary,
        "boards": results,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=4)


def make_project_output_paths(directory):
    return {
        "json": os.path.join(directory, "silicore_project_summary.json"),
        "md": os.path.join(directory, "silicore_project_summary.md"),
        "html": os.path.join(directory, "silicore_project_summary.html"),
    }