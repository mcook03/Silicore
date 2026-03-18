from collections import Counter, defaultdict

from engine.report_utils import sort_risks_for_reporting, summarize_top_categories


def generate_report(pcb, risks, score):
    lines = []

    severity_counter = Counter()
    category_counter = Counter()
    grouped = defaultdict(list)

    sorted_risks = sort_risks_for_reporting(risks)

    for risk in sorted_risks:
        severity = risk.get("severity", "low")
        category = risk.get("category", "other")
        severity_counter[severity] += 1
        category_counter[category] += 1
        grouped[category].append(risk)

    top_categories = summarize_top_categories(category_counter, limit=3)
    top_fixes = sorted_risks[:5]

    lines.append("SILICORE ENGINEERING REPORT")
    lines.append("=" * 40)
    lines.append("")
    lines.append("EXECUTIVE SUMMARY")
    lines.append("-" * 40)
    lines.append(f"Overall Risk Score: {score} / 10")
    lines.append(f"Total Risks: {len(risks)}")
    lines.append(
        f"Critical/High Risks: {severity_counter['critical'] + severity_counter['high']}"
    )

    if top_categories:
        lines.append(
            "Most Affected Categories: "
            + ", ".join(f"{name} ({count})" for name, count in top_categories)
        )
    else:
        lines.append("Most Affected Categories: None")

    if top_fixes:
        lines.append("Top Priority Fixes:")
        for risk in top_fixes:
            lines.append(f"- {risk['short_title']}")
    else:
        lines.append("Top Priority Fixes: None")

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
    lines.append("")
    lines.append("RISK SUMMARY")
    lines.append("-" * 40)
    lines.append(f"Critical: {severity_counter['critical']}")
    lines.append(f"High: {severity_counter['high']}")
    lines.append(f"Medium: {severity_counter['medium']}")
    lines.append(f"Low: {severity_counter['low']}")
    lines.append("")
    lines.append("RISKS BY CATEGORY")
    lines.append("-" * 40)

    if category_counter:
        for category, count in sorted(category_counter.items()):
            lines.append(f"{category}: {count}")
    else:
        lines.append("No risks found.")

    lines.append("")
    lines.append("TOP PRIORITY ISSUES")
    lines.append("-" * 40)

    if top_fixes:
        for risk in top_fixes:
            lines.append(f"- [{risk['severity'].upper()}] {risk['message']}")
            if risk.get("why_it_matters"):
                lines.append(f"  Why It Matters: {risk['why_it_matters']}")
            if risk.get("recommendation"):
                lines.append(f"  Recommendation: {risk['recommendation']}")
    else:
        lines.append("No priority issues found.")

    lines.append("")
    lines.append("DETAILED FINDINGS")
    lines.append("-" * 40)
    lines.append("")

    for category in sorted(grouped.keys()):
        items = grouped[category]
        lines.append(f"[{category.upper()}]")

        for risk in items:
            lines.append(f"- ({risk['severity'].upper()}) {risk['message']}")
            lines.append(f"  Title: {risk.get('short_title', risk['message'])}")

            if risk.get("components"):
                lines.append(f"  Components: {', '.join(risk['components'])}")

            if risk.get("nets"):
                lines.append(f"  Nets: {', '.join(risk['nets'])}")

            if risk.get("region"):
                lines.append(f"  Region: {risk['region']}")

            lines.append(f"  Confidence: {risk.get('confidence', 0.0)}")
            lines.append(f"  Fix Priority: {risk.get('fix_priority', 'medium')}")
            lines.append(f"  Estimated Impact: {risk.get('estimated_impact', 'moderate')}")
            lines.append(f"  Design Domain: {risk.get('design_domain', 'general')}")

            if risk.get("why_it_matters"):
                lines.append(f"  Why It Matters: {risk['why_it_matters']}")

            if risk.get("recommendation"):
                lines.append(f"  Recommendation: {risk['recommendation']}")

            actions = risk.get("suggested_actions", [])
            if actions:
                lines.append("  Suggested Actions:")
                for action in actions:
                    lines.append(f"    - {action}")

            metrics = risk.get("metrics", {})
            if metrics:
                lines.append(f"  Metrics: {metrics}")

        lines.append("")

    lines.append("END OF REPORT")

    return "\n".join(lines)