from collections import defaultdict


def generate_report(pcb, risks, score):
    lines = []

    lines.append("SILICORE ENGINEERING REPORT")
    lines.append("=" * 40)
    lines.append("")

    lines.append("BOARD OVERVIEW")
    lines.append("-" * 40)
    lines.append(f"Total Components: {len(pcb.components)}")
    lines.append(f"Total Nets: {len(pcb.nets)}")
    lines.append(f"Overall Risk Score: {score} / 10")
    lines.append("")

    if not risks:
        lines.append("No design risks found.")
        return "\n".join(lines)

    severity_counts = defaultdict(int)
    category_counts = defaultdict(int)

    for risk in risks:
        severity_counts[risk["severity"]] += 1
        category_counts[risk["category"]] += 1

    lines.append("RISK SUMMARY")
    lines.append("-" * 40)
    lines.append(f"Total Risks: {len(risks)}")
    lines.append(f"Critical: {severity_counts['critical']}")
    lines.append(f"High: {severity_counts['high']}")
    lines.append(f"Medium: {severity_counts['medium']}")
    lines.append(f"Low: {severity_counts['low']}")
    lines.append("")

    lines.append("RISKS BY CATEGORY")
    lines.append("-" * 40)
    for category, count in sorted(category_counts.items()):
        lines.append(f"{category}: {count}")
    lines.append("")

    grouped = defaultdict(list)
    for risk in risks:
        grouped[risk["category"]].append(risk)

    lines.append("DETAILED FINDINGS")
    lines.append("-" * 40)

    for category, category_risks in sorted(grouped.items()):
        lines.append("")
        lines.append(f"[{category.upper()}]")

        for risk in category_risks:
            lines.append(f"- ({risk['severity'].upper()}) {risk['message']}")

            if risk.get("components"):
                lines.append(f"  Components: {', '.join(risk['components'])}")

            if risk.get("nets"):
                lines.append(f"  Nets: {', '.join(risk['nets'])}")

            if risk.get("region"):
                lines.append(f"  Region: {risk['region']}")

            if risk.get("recommendation"):
                lines.append(f"  Recommendation: {risk['recommendation']}")

    lines.append("")
    lines.append("TOP PRIORITY ISSUES")
    lines.append("-" * 40)

    severity_rank = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    sorted_risks = sorted(
        risks,
        key=lambda r: severity_rank.get(r["severity"], 0),
        reverse=True
    )

    for risk in sorted_risks[:5]:
        lines.append(f"- [{risk['severity'].upper()}] {risk['message']}")

    lines.append("")
    lines.append("END OF REPORT")

    return "\n".join(lines)