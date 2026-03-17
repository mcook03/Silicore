from collections import Counter, defaultdict


def generate_report(pcb, risks, score):
    lines = []

    severity_counter = Counter()
    category_counter = Counter()
    grouped = defaultdict(list)

    for risk in risks:
        severity = risk.get("severity", "low")
        category = risk.get("category", "other")
        severity_counter[severity] += 1
        category_counter[category] += 1
        grouped[category].append(risk)

    lines.append("SILICORE ENGINEERING REPORT")
    lines.append("=" * 40)
    lines.append("")
    lines.append("BOARD OVERVIEW")
    lines.append("-" * 40)
    lines.append(f"Source Format: {pcb.source_format}")
    lines.append(f"Total Components: {len(pcb.components)}")
    lines.append(f"Total Nets: {len(pcb.nets)}")
    lines.append(f"Total Traces: {len(pcb.traces)}")
    lines.append(f"Total Vias: {len(pcb.vias)}")
    lines.append(f"Board Size Estimate: {round(pcb.board_width, 2)} x {round(pcb.board_height, 2)}")
    lines.append(f"Layers: {', '.join(sorted(list(pcb.layers))) if pcb.layers else 'None'}")
    lines.append(f"Overall Risk Score: {score} / 10")
    lines.append("")
    lines.append("RISK SUMMARY")
    lines.append("-" * 40)
    lines.append(f"Total Risks: {len(risks)}")
    lines.append(f"Critical: {severity_counter['critical']}")
    lines.append(f"High: {severity_counter['high']}")
    lines.append(f"Medium: {severity_counter['medium']}")
    lines.append(f"Low: {severity_counter['low']}")
    lines.append("")
    lines.append("RISKS BY CATEGORY")
    lines.append("-" * 40)
    for category, count in sorted(category_counter.items()):
        lines.append(f"{category}: {count}")
    lines.append("")
    lines.append("DETAILED FINDINGS")
    lines.append("-" * 40)
    lines.append("")

    for category, items in grouped.items():
        lines.append(f"[{category.upper()}]")
        for risk in items:
            lines.append(f"- ({risk['severity'].upper()}) {risk['message']}")
            if risk.get("short_title"):
                lines.append(f"  Title: {risk['short_title']}")
            if risk.get("components"):
                lines.append(f"  Components: {', '.join(risk['components'])}")
            if risk.get("nets"):
                lines.append(f"  Nets: {', '.join(risk['nets'])}")
            if risk.get("region"):
                lines.append(f"  Region: {risk['region']}")
            if risk.get("confidence") is not None:
                lines.append(f"  Confidence: {risk['confidence']}")
            if risk.get("fix_priority"):
                lines.append(f"  Fix Priority: {risk['fix_priority']}")
            if risk.get("estimated_impact"):
                lines.append(f"  Estimated Impact: {risk['estimated_impact']}")
            if risk.get("recommendation"):
                lines.append(f"  Recommendation: {risk['recommendation']}")
        lines.append("")

    lines.append("TOP PRIORITY ISSUES")
    lines.append("-" * 40)

    sorted_risks = sorted(
        risks,
        key=lambda r: (
            {"critical": 4, "high": 3, "medium": 2, "low": 1}.get(r.get("severity", "low"), 1),
            r.get("confidence", 0.0),
        ),
        reverse=True,
    )

    for risk in sorted_risks[:5]:
        lines.append(f"- [{risk['severity'].upper()}] {risk['message']}")

    lines.append("")
    lines.append("END OF REPORT")

    return "\n".join(lines)