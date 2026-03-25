def generate_report(pcb, analysis_result):
    lines = []

    lines.append("# SILICORE ENGINEERING REPORT")
    lines.append("")

    lines.append("## BOARD OVERVIEW")
    lines.append(f"- Total Components: {len(getattr(pcb, 'components', []))}")
    lines.append(f"- Total Nets: {len(getattr(pcb, 'nets', {}))}")
    lines.append(f"- Overall Risk Score: {analysis_result.get('score', 0)} / 10")
    lines.append("")

    risk_summary = analysis_result.get("risk_summary", {})
    by_severity = risk_summary.get("by_severity", {})
    by_category = risk_summary.get("by_category", {})

    lines.append("## RISK SUMMARY")
    lines.append(f"- Total Risks: {risk_summary.get('total_risks', 0)}")
    lines.append(f"- Low: {by_severity.get('low', 0)}")
    lines.append(f"- Medium: {by_severity.get('medium', 0)}")
    lines.append(f"- High: {by_severity.get('high', 0)}")
    lines.append(f"- Critical: {by_severity.get('critical', 0)}")
    lines.append("")

    lines.append("## RISKS BY CATEGORY")
    if by_category:
        for category, count in sorted(by_category.items()):
            lines.append(f"- {category}: {count}")
    else:
        lines.append("- No category risks found")
    lines.append("")

    score_explanation = analysis_result.get("score_explanation", {})

    lines.append("## SCORE EXPLAINABILITY")
    lines.append(f"- Start Score: {score_explanation.get('start_score', 10.0)}")
    lines.append(f"- Total Penalty: {score_explanation.get('total_penalty', 0.0)}")
    lines.append(f"- Final Score: {score_explanation.get('final_score', analysis_result.get('score', 0))}")
    lines.append("")

    lines.append("### Penalties by Severity")
    severity_totals = score_explanation.get("severity_totals", {})
    if severity_totals:
        for severity, penalty in sorted(severity_totals.items()):
            lines.append(f"- {severity}: {penalty}")
    else:
        lines.append("- No severity penalties")
    lines.append("")

    lines.append("### Penalties by Category")
    category_totals = score_explanation.get("category_totals", {})
    if category_totals:
        for category, penalty in sorted(category_totals.items()):
            lines.append(f"- {category}: {penalty}")
    else:
        lines.append("- No category penalties")
    lines.append("")

    lines.append("## DETAILED FINDINGS")
    risks = analysis_result.get("risks", [])
    if risks:
        for risk in risks:
            lines.append(f"### [{str(risk.get('severity', 'low')).upper()}] {risk.get('message', 'No message')}")
            lines.append(f"- Rule ID: {risk.get('rule_id', 'UNKNOWN_RULE')}")
            lines.append(f"- Category: {risk.get('category', 'uncategorized')}")
            if risk.get("components"):
                lines.append(f"- Components: {', '.join(risk.get('components', []))}")
            if risk.get("nets"):
                lines.append(f"- Nets: {', '.join(risk.get('nets', []))}")
            if risk.get("metrics"):
                lines.append(f"- Metrics: {risk.get('metrics')}")
            lines.append(f"- Recommendation: {risk.get('recommendation', 'No recommendation provided')}")
            lines.append("")
    else:
        lines.append("- No risks found")
        lines.append("")

    lines.append("## DETAILED PENALTY BREAKDOWN")
    detailed_penalties = score_explanation.get("detailed_penalties", [])
    if detailed_penalties:
        for item in detailed_penalties:
            lines.append(
                f"- {item.get('rule_id', 'UNKNOWN_RULE')} | "
                f"{item.get('severity', 'low')} | "
                f"{item.get('category', 'uncategorized')} | "
                f"Penalty: {item.get('penalty', 0)} | "
                f"{item.get('message', 'No message')}"
            )
    else:
        lines.append("- No penalties recorded")

    return "\n".join(lines)