import json


def export_analysis_to_json(pcb, risks, score, output_file="analysis.json"):
    severity_counts = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
    }

    for risk in risks:
        severity = risk.get("severity", "low")
        if severity in severity_counts:
            severity_counts[severity] += 1

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
            "total_risks": len(risks),
            "severity_counts": severity_counts,
            "layers": sorted(list(pcb.layers)),
        },
        "pcb": pcb.to_dict(),
        "risks": risks,
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)