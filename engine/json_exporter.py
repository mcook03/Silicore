import json

from engine.report_utils import sort_risks_for_reporting


def export_analysis_to_json(pcb, risks, score, output_file="analysis.json"):
    severity_counts = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
    }

    category_counts = {}

    sorted_risks = sort_risks_for_reporting(risks)

    for risk in sorted_risks:
        severity = risk.get("severity", "low")
        category = risk.get("category", "other")

        if severity in severity_counts:
            severity_counts[severity] += 1

        if category not in category_counts:
            category_counts[category] = 0
        category_counts[category] += 1

    data = {
        "summary": {
            "source_format": pcb.source_format,
            "total_components": len(pcb.components),
            "total_nets": len(pcb.nets),
            "total_traces": len(pcb.traces),
            "total_vias": len(pcb.vias),
            "total_zones": len(pcb.zones),
            "board_width": pcb.board_width,
            "board_height": pcb.board_height,
            "risk_score": score,
            "total_risks": len(sorted_risks),
            "severity_counts": severity_counts,
            "category_counts": category_counts,
            "layers": sorted(list(pcb.layers)),
        },
        "top_issues": sorted_risks[:5],
        "pcb": pcb.to_dict(),
        "risks": sorted_risks,
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)