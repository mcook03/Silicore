import importlib
import inspect
import json
import os
import shutil
from collections import defaultdict
from datetime import datetime
from html import escape

from engine.config_loader import load_config, get_editable_config_view
from engine.dashboard_storage import (
    ensure_runs_folder,
    create_run_directory,
    save_run_meta,
)

SUPPORTED_EXTENSIONS = {".txt", ".kicad_pcb"}


def ensure_clean_upload_dir(upload_folder):
    if os.path.exists(upload_folder):
        shutil.rmtree(upload_folder)
    os.makedirs(upload_folder, exist_ok=True)


def safe_filename(filename):
    return filename.replace("/", "_").replace("\\", "_").strip()


def build_single_downloads(run_dir_name):
    return [
        {"label": "Download JSON", "url": f"/download/{run_dir_name}/single_analysis.json"},
        {"label": "Download Markdown", "url": f"/download/{run_dir_name}/single_report.md"},
        {"label": "Download HTML", "url": f"/download/{run_dir_name}/single_report.html"},
    ]


def build_project_downloads(run_dir_name):
    return [
        {"label": "Download JSON", "url": f"/download/{run_dir_name}/project_summary.json"},
        {"label": "Download Markdown", "url": f"/download/{run_dir_name}/project_summary.md"},
        {"label": "Download HTML", "url": f"/download/{run_dir_name}/project_summary.html"},
    ]


def get_dashboard_config(config_path):
    config = load_config(config_path)
    return config, get_editable_config_view(config)


def _optional_function(module_name, function_names):
    try:
        module = importlib.import_module(module_name)
    except Exception:
        return None

    for name in function_names:
        if hasattr(module, name):
            return getattr(module, name)

    return None


def _call_with_supported_args(func, **kwargs):
    signature = inspect.signature(func)
    parameters = signature.parameters
    accepted = {}

    for name, value in kwargs.items():
        if name in parameters:
            accepted[name] = value

    if accepted:
        return func(**accepted)

    if len(parameters) == 1 and kwargs:
        first_value = next(iter(kwargs.values()))
        return func(first_value)

    return func()


def _safe_explain_risk(risk):
    explain_func = _optional_function(
        "engine.explainability_engine",
        ["explain_risk"],
    )
    if explain_func is None:
        return {
            "root_cause": "General design issue",
            "impact": "Unknown system impact",
            "confidence": risk.get("confidence", 0.5),
        }

    try:
        explanation = explain_func(risk)
        if isinstance(explanation, dict):
            return {
                "root_cause": explanation.get("root_cause", "General design issue"),
                "impact": explanation.get("impact", "Unknown system impact"),
                "confidence": explanation.get("confidence", risk.get("confidence", 0.5)),
            }
    except Exception:
        pass

    return {
        "root_cause": "General design issue",
        "impact": "Unknown system impact",
        "confidence": risk.get("confidence", 0.5),
    }


def _safe_suggest_fix(risk):
    fix_func = _optional_function(
        "engine.fix_engine",
        ["suggest_fix"],
    )
    if fix_func is None:
        return {
            "fix": risk.get("recommendation", "Manual review required"),
            "priority": risk.get("fix_priority", "medium"),
        }

    try:
        suggestion = fix_func(risk)
        if isinstance(suggestion, dict):
            return {
                "fix": suggestion.get("fix", risk.get("recommendation", "Manual review required")),
                "priority": suggestion.get("priority", risk.get("fix_priority", "medium")),
            }
    except Exception:
        pass

    return {
        "fix": risk.get("recommendation", "Manual review required"),
        "priority": risk.get("fix_priority", "medium"),
    }


def _normalize_risk(risk):
    if not isinstance(risk, dict):
        normalized = {
            "rule_id": None,
            "category": "unknown",
            "severity": "low",
            "message": str(risk),
            "recommendation": "Review this finding.",
            "components": [],
            "nets": [],
            "region": None,
            "metrics": {},
        }
        normalized["explanation"] = _safe_explain_risk(normalized)
        normalized["fix_suggestion"] = _safe_suggest_fix(normalized)
        return normalized

    normalized = {
        "rule_id": risk.get("rule_id"),
        "category": risk.get("category", "unknown"),
        "severity": risk.get("severity", "low"),
        "message": risk.get("message", "No message provided."),
        "recommendation": risk.get("recommendation", "Review this finding."),
        "components": risk.get("components", []),
        "nets": risk.get("nets", []),
        "region": risk.get("region"),
        "metrics": risk.get("metrics", {}),
    }

    if isinstance(risk.get("explanation"), dict):
        normalized["explanation"] = {
            "root_cause": risk["explanation"].get("root_cause", "General design issue"),
            "impact": risk["explanation"].get("impact", "Unknown system impact"),
            "confidence": risk["explanation"].get("confidence", risk.get("confidence", 0.5)),
        }
    else:
        normalized["explanation"] = _safe_explain_risk(normalized)

    if isinstance(risk.get("fix_suggestion"), dict):
        normalized["fix_suggestion"] = {
            "fix": risk["fix_suggestion"].get("fix", normalized["recommendation"]),
            "priority": risk["fix_suggestion"].get("priority", risk.get("fix_priority", "medium")),
        }
    else:
        normalized["fix_suggestion"] = _safe_suggest_fix(normalized)

    return normalized


def _severity_penalty_map(config):
    return config.get("score", {}).get(
        "severity_penalties",
        {
            "low": 0.5,
            "medium": 1.0,
            "high": 1.5,
            "critical": 2.0,
        },
    )


def _severity_rank(severity):
    order = {
        "critical": 0,
        "high": 1,
        "medium": 2,
        "low": 3,
    }
    return order.get(str(severity).lower(), 4)


def _compute_score_and_explanation(risks, config):
    score_config = config.get("score", {})
    start_score = float(score_config.get("start_score", 10.0))
    min_score = float(score_config.get("min_score", 0.0))
    max_score = float(score_config.get("max_score", 10.0))
    severity_penalties = _severity_penalty_map(config)

    severity_totals = {}
    category_totals = {}
    details = []
    total_penalty = 0.0

    for risk in risks:
        severity = str(risk.get("severity", "low")).lower()
        category = str(risk.get("category", "unknown"))
        penalty = float(severity_penalties.get(severity, 0.0))

        total_penalty += penalty
        severity_totals[severity] = round(severity_totals.get(severity, 0.0) + penalty, 2)
        category_totals[category] = round(category_totals.get(category, 0.0) + penalty, 2)

        details.append(
            {
                "severity": severity,
                "category": category,
                "penalty": penalty,
                "message": risk.get("message", ""),
                "root_cause": risk.get("explanation", {}).get("root_cause", ""),
                "impact": risk.get("explanation", {}).get("impact", ""),
                "confidence": risk.get("explanation", {}).get("confidence"),
                "suggested_fix": risk.get("fix_suggestion", {}).get("fix", ""),
                "fix_priority": risk.get("fix_suggestion", {}).get("priority", ""),
            }
        )

    score = start_score - total_penalty
    score = max(min_score, min(max_score, score))
    score = round(score, 2)

    return score, {
        "start_score": start_score,
        "total_penalty": round(total_penalty, 2),
        "final_score": score,
        "severity_totals": severity_totals,
        "category_totals": category_totals,
        "details": details,
    }


def _extract_components(pcb):
    if hasattr(pcb, "components") and isinstance(pcb.components, list):
        return pcb.components

    if isinstance(pcb, dict) and "components" in pcb and isinstance(pcb["components"], list):
        return pcb["components"]

    return []


def _extract_nets(pcb):
    if hasattr(pcb, "nets"):
        nets = getattr(pcb, "nets")
        if isinstance(nets, list):
            return nets
        if isinstance(nets, dict):
            return list(nets.keys())

    if isinstance(pcb, dict) and "nets" in pcb:
        nets = pcb["nets"]
        if isinstance(nets, list):
            return nets
        if isinstance(nets, dict):
            return list(nets.keys())

    return []


def _component_ref(component):
    if isinstance(component, dict):
        return (
            component.get("ref")
            or component.get("reference")
            or component.get("name")
            or "UNKNOWN"
        )

    return (
        getattr(component, "ref", None)
        or getattr(component, "reference", None)
        or getattr(component, "name", None)
        or "UNKNOWN"
    )


def _build_board_summary(pcb, risks, filename):
    components = _extract_components(pcb)
    nets = _extract_nets(pcb)

    severity_counts = {}
    for risk in risks:
        severity = str(risk.get("severity", "unknown")).lower()
        severity_counts[severity] = severity_counts.get(severity, 0) + 1

    component_refs = [_component_ref(component) for component in components[:10]]

    return {
        "filename": filename,
        "component_count": len(components),
        "net_count": len(nets),
        "sample_components": component_refs,
        "risk_count": len(risks),
        "severity_counts": severity_counts,
    }


def _group_risks_by_category(risks):
    grouped = defaultdict(list)
    for risk in risks:
        grouped[str(risk.get("category", "unknown"))].append(risk)

    grouped_sections = []
    for category, items in grouped.items():
        items_sorted = sorted(
            items,
            key=lambda item: (
                _severity_rank(item.get("severity")),
                item.get("message", ""),
            ),
        )
        grouped_sections.append(
            {
                "category": category,
                "title": category.replace("_", " ").title(),
                "count": len(items_sorted),
                "risks": items_sorted,
            }
        )

    grouped_sections.sort(
        key=lambda section: (
            min([_severity_rank(risk.get("severity")) for risk in section["risks"]] or [99]),
            section["title"],
        )
    )
    return grouped_sections


def _top_issues(risks, limit=3):
    return sorted(
        risks,
        key=lambda item: (
            _severity_rank(item.get("severity")),
            item.get("category", ""),
            item.get("message", ""),
        ),
    )[:limit]


def _score_label(score):
    try:
        score_value = float(score)
    except (TypeError, ValueError):
        score_value = 0.0

    if score_value >= 8.5:
        return "Strong engineering position"
    if score_value >= 7.0:
        return "Good with targeted issues"
    if score_value >= 5.0:
        return "Needs review before release"
    return "High engineering risk"


def _health_summary(score, risks):
    score_value = float(score)
    critical_count = sum(
        1 for risk in risks if str(risk.get("severity", "")).lower() == "critical"
    )
    high_count = sum(
        1 for risk in risks if str(risk.get("severity", "")).lower() == "high"
    )

    if score_value >= 8.5 and critical_count == 0:
        return {
            "title": "Strong board health",
            "summary": "This board looks strong overall. The remaining issues appear targeted rather than systemic.",
        }
    if critical_count > 0:
        return {
            "title": "Critical review needed",
            "summary": "Critical findings are present and should be reviewed before release decisions.",
        }
    if score_value < 5.0 or high_count >= 3:
        return {
            "title": "Needs engineering attention",
            "summary": "This board has several high-impact findings that deserve active cleanup.",
        }
    if not risks:
        return {
            "title": "No issues detected",
            "summary": "No findings were produced under the current ruleset and configuration.",
        }
    return {
        "title": "Moderate review recommended",
        "summary": "The board is workable, but still has meaningful issues worth addressing.",
    }


def _load_board(file_path):
    extension = os.path.splitext(file_path)[1].lower()

    if extension == ".kicad_pcb":
        parser_func = _optional_function(
            "engine.kicad_parser",
            ["parse_kicad_pcb", "parse_kicad_file", "parse_board"],
        )
        if parser_func:
            return _call_with_supported_args(
                parser_func,
                file_path=file_path,
                path=file_path,
                filename=file_path,
            )

    parser_func = _optional_function(
        "engine.parser",
        ["parse_pcb_file", "parse_file", "load_pcb", "parse_board"],
    )
    if parser_func:
        return _call_with_supported_args(
            parser_func,
            file_path=file_path,
            path=file_path,
            filename=file_path,
        )

    raise RuntimeError("No compatible board parser was found.")


def _normalize_board(pcb):
    normalize_func = _optional_function(
        "engine.normalizer",
        ["normalize_pcb", "normalize_board"],
    )
    if not normalize_func:
        return pcb

    try:
        normalized = _call_with_supported_args(
            normalize_func,
            pcb=pcb,
            board=pcb,
        )
        return normalized if normalized is not None else pcb
    except Exception:
        return pcb


def _run_rule_engine(pcb, config):
    rule_func = _optional_function(
        "engine.rule_runner",
        ["run_analysis", "run_rule_engine", "run_rules"],
    )
    if not rule_func:
        raise RuntimeError("No compatible rule runner was found.")

    result = _call_with_supported_args(
        rule_func,
        pcb=pcb,
        board=pcb,
        config=config,
    )

    if isinstance(result, dict):
        risks = result.get("risks")
        if risks is None and "findings" in result:
            risks = result.get("findings")
        if risks is None:
            risks = []
        return [_normalize_risk(risk) for risk in risks], result

    if isinstance(result, list):
        return [_normalize_risk(risk) for risk in result], {}

    return [], {}


def _write_json(path, data):
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


def _write_single_markdown(path, result):
    grouped = _group_risks_by_category(result["risks"])
    top_issues = _top_issues(result["risks"])
    health = _health_summary(result["score"], result["risks"])
    board_summary = result.get("board_summary", {})
    score_explanation = result.get("score_explanation", {})

    lines = [
        "# SILICORE ENGINEERING REPORT",
        "",
        f"**File:** {result['filename']}",
        f"**Score:** {result['score']} / 10",
        f"**Health:** {_score_label(result['score'])}",
        "",
        "## Executive Summary",
        "",
        f"**{health['title']}**",
        "",
        health["summary"],
        "",
        "## Board Overview",
        "",
        f"- Components: {board_summary.get('component_count', 0)}",
        f"- Nets: {board_summary.get('net_count', 0)}",
        f"- Total Risks: {len(result['risks'])}",
        f"- Total Penalty: {score_explanation.get('total_penalty', 0)}",
        "",
        "## Top Issues",
        "",
    ]

    if top_issues:
        for issue in top_issues:
            lines.append(
                f"- **[{str(issue.get('severity', 'low')).upper()}]** "
                f"{issue.get('message', 'No message')}"
            )
    else:
        lines.append("- No issues detected")

    lines.extend(
        [
            "",
            "## Score Breakdown",
            "",
            f"- Start Score: {score_explanation.get('start_score', 10)}",
            f"- Total Penalty: {score_explanation.get('total_penalty', 0)}",
            f"- Final Score: {score_explanation.get('final_score', result['score'])}",
            "",
            "### Severity Penalties",
            "",
        ]
    )

    severity_totals = score_explanation.get("severity_totals", {})
    if severity_totals:
        for severity, value in severity_totals.items():
            lines.append(f"- {severity}: {value}")
    else:
        lines.append("- None")

    lines.extend(["", "### Category Penalties", ""])
    category_totals = score_explanation.get("category_totals", {})
    if category_totals:
        for category, value in category_totals.items():
            lines.append(f"- {category}: {value}")
    else:
        lines.append("- None")

    lines.extend(["", "## Grouped Findings", ""])
    if grouped:
        for section in grouped:
            lines.append(f"### {section['title']} ({section['count']})")
            lines.append("")
            for risk in section["risks"]:
                lines.append(
                    f"- **[{str(risk.get('severity', 'low')).upper()}]** "
                    f"{risk.get('message', 'No message')}"
                )
                lines.append(f"  - Recommendation: {risk.get('recommendation', 'Manual review required')}")
                explanation = risk.get("explanation", {})
                if explanation:
                    lines.append(f"  - Root Cause: {explanation.get('root_cause', 'Unknown')}")
                    lines.append(f"  - Impact: {explanation.get('impact', 'Unknown')}")
                fix_suggestion = risk.get("fix_suggestion", {})
                if fix_suggestion:
                    lines.append(f"  - Suggested Fix: {fix_suggestion.get('fix', 'Manual review required')}")
                    lines.append(f"  - Fix Priority: {fix_suggestion.get('priority', 'medium')}")
                if risk.get("components"):
                    lines.append(f"  - Components: {', '.join(risk['components'])}")
                if risk.get("nets"):
                    lines.append(f"  - Nets: {', '.join(risk['nets'])}")
                lines.append("")
    else:
        lines.append("No risks detected.")

    with open(path, "w", encoding="utf-8") as file:
        file.write("\n".join(lines))


def _write_single_html(path, result):
    grouped = _group_risks_by_category(result["risks"])
    top_issues = _top_issues(result["risks"])
    health = _health_summary(result["score"], result["risks"])
    board_summary = result.get("board_summary", {})
    score_explanation = result.get("score_explanation", {})

    def sev_class(severity):
        severity = str(severity).lower()
        if severity == "critical":
            return "critical"
        if severity == "high":
            return "high"
        if severity == "medium":
            return "medium"
        return "low"

    top_issues_html = ""
    if top_issues:
        for issue in top_issues:
            top_issues_html += f"""
            <div class="issue-card">
                <div class="pill {sev_class(issue.get('severity'))}">{escape(str(issue.get('severity', 'low')).upper())}</div>
                <div class="issue-title">{escape(str(issue.get('message', 'No message')))}</div>
                <div class="issue-meta">{escape(str(issue.get('category', 'unknown')).replace('_', ' ').title())}</div>
            </div>
            """
    else:
        top_issues_html = "<div class='empty'>No issues detected.</div>"

    grouped_html = ""
    if grouped:
        for section in grouped:
            risks_html = ""
            for risk in section["risks"]:
                explanation = risk.get("explanation", {})
                fix_suggestion = risk.get("fix_suggestion", {})
                components_html = ""
                nets_html = ""

                if risk.get("components"):
                    components_html = f"<div class='meta-chip'>Components: {escape(', '.join(risk['components']))}</div>"
                if risk.get("nets"):
                    nets_html = f"<div class='meta-chip'>Nets: {escape(', '.join(risk['nets']))}</div>"

                risks_html += f"""
                <div class="finding-card">
                    <div class="finding-top">
                        <div class="pill {sev_class(risk.get('severity'))}">{escape(str(risk.get('severity', 'low')).upper())}</div>
                        <div class="finding-title">{escape(str(risk.get('message', 'No message')))}</div>
                        <div class="finding-meta">Rule: {escape(str(risk.get('rule_id', 'UNKNOWN_RULE')))}</div>
                    </div>
                    <div class="finding-box">
                        <strong>Recommendation:</strong> {escape(str(risk.get('recommendation', 'Manual review required')))}
                    </div>
                    <div class="finding-box">
                        <strong>Root Cause:</strong> {escape(str(explanation.get('root_cause', 'Unknown')))}<br>
                        <strong>Impact:</strong> {escape(str(explanation.get('impact', 'Unknown')))}<br>
                        <strong>Suggested Fix:</strong> {escape(str(fix_suggestion.get('fix', 'Manual review required')))}
                    </div>
                    <div class="meta-row">
                        {components_html}
                        {nets_html}
                    </div>
                </div>
                """

            grouped_html += f"""
            <section class="category-section">
                <div class="section-header">
                    <h3>{escape(section['title'])}</h3>
                    <span class="count-badge">{section['count']} finding(s)</span>
                </div>
                {risks_html}
            </section>
            """
    else:
        grouped_html = "<div class='empty'>No grouped findings.</div>"

    severity_items = ""
    for severity, value in score_explanation.get("severity_totals", {}).items():
        severity_items += f"<div class='mini-line'>{escape(str(severity))}: {value}</div>"
    if not severity_items:
        severity_items = "<div class='mini-line'>None</div>"

    category_items = ""
    for category, value in score_explanation.get("category_totals", {}).items():
        category_items += f"<div class='mini-line'>{escape(str(category))}: {value}</div>"
    if not category_items:
        category_items = "<div class='mini-line'>None</div>"

    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Silicore Engineering Report</title>
    <style>
        body {{
            margin: 0;
            padding: 32px;
            background: #0b1020;
            color: #e8edf7;
            font-family: Arial, Helvetica, sans-serif;
        }}
        .page {{
            max-width: 1100px;
            margin: 0 auto;
        }}
        .hero, .panel, .category-section {{
            background: #141b2d;
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 18px;
            padding: 20px;
            margin-bottom: 18px;
        }}
        .hero h1 {{
            margin: 0 0 8px;
            font-size: 32px;
        }}
        .subtle {{
            color: #aab6d3;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 12px;
            margin-top: 18px;
        }}
        .stat {{
            background: rgba(255,255,255,0.04);
            border-radius: 14px;
            padding: 14px;
        }}
        .stat-label {{
            font-size: 12px;
            text-transform: uppercase;
            color: #aab6d3;
            margin-bottom: 6px;
        }}
        .stat-value {{
            font-size: 28px;
            font-weight: bold;
        }}
        .grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
        }}
        .issue-card, .finding-card {{
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 14px;
            padding: 14px;
            margin-top: 12px;
        }}
        .pill {{
            display: inline-block;
            padding: 6px 10px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        .critical {{ background: rgba(255,77,109,0.14); color: #ffd6dd; }}
        .high {{ background: rgba(255,107,107,0.14); color: #ffdfe1; }}
        .medium {{ background: rgba(255,204,102,0.14); color: #fff1cc; }}
        .low {{ background: rgba(93,211,158,0.14); color: #d8ffee; }}
        .issue-title, .finding-title {{
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 6px;
        }}
        .issue-meta, .finding-meta {{
            color: #aab6d3;
            font-size: 13px;
        }}
        .finding-box {{
            margin-top: 10px;
            background: rgba(255,255,255,0.03);
            border-radius: 10px;
            padding: 10px 12px;
            line-height: 1.6;
        }}
        .meta-row {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 12px;
        }}
        .meta-chip, .count-badge {{
            background: rgba(255,255,255,0.05);
            border-radius: 999px;
            padding: 7px 10px;
            font-size: 12px;
        }}
        .section-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 10px;
        }}
        .mini-line {{
            margin-top: 8px;
            color: #e8edf7;
        }}
        .empty {{
            color: #aab6d3;
            margin-top: 12px;
        }}
    </style>
</head>
<body>
    <div class="page">
        <section class="hero">
            <h1>Silicore Engineering Report</h1>
            <div class="subtle">{escape(result['filename'])}</div>
            <p class="subtle" style="margin-top: 10px;">
                <strong>{escape(health['title'])}</strong><br>
                {escape(health['summary'])}
            </p>

            <div class="stats">
                <div class="stat">
                    <div class="stat-label">Score</div>
                    <div class="stat-value">{result['score']}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Components</div>
                    <div class="stat-value">{board_summary.get('component_count', 0)}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Nets</div>
                    <div class="stat-value">{board_summary.get('net_count', 0)}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Total Risks</div>
                    <div class="stat-value">{len(result['risks'])}</div>
                </div>
            </div>
        </section>

        <div class="grid">
            <section class="panel">
                <h2>Top Issues</h2>
                {top_issues_html}
            </section>

            <section class="panel">
                <h2>Score Breakdown</h2>
                <div class="mini-line">Start Score: {score_explanation.get('start_score', 10)}</div>
                <div class="mini-line">Total Penalty: {score_explanation.get('total_penalty', 0)}</div>
                <div class="mini-line">Final Score: {score_explanation.get('final_score', result['score'])}</div>
                <h3 style="margin-top: 18px;">Severity Penalties</h3>
                {severity_items}
                <h3 style="margin-top: 18px;">Category Penalties</h3>
                {category_items}
            </section>
        </div>

        <section class="panel">
            <h2>Grouped Findings</h2>
            {grouped_html}
        </section>
    </div>
</body>
</html>
"""

    with open(path, "w", encoding="utf-8") as file:
        file.write(html)


def _write_project_markdown(path, summary, boards):
    lines = [
        "# SILICORE PROJECT SUMMARY",
        "",
        f"**Total Boards:** {summary['total_boards']}",
        f"**Average Score:** {summary['average_score']} / 10",
        f"**Best Score:** {summary['best_score']} / 10",
        f"**Worst Score:** {summary['worst_score']} / 10",
        "",
        "## Ranked Boards",
        "",
    ]

    for index, board in enumerate(boards, start=1):
        health = _health_summary(board["score"], board["risks"])
        lines.append(f"### #{index} {board['filename']}")
        lines.append(f"- Score: {board['score']} / 10")
        lines.append(f"- Summary: {health['title']}")
        lines.append(f"- Notes: {health['summary']}")
        lines.append("- Top Issues:")
        issues = _top_issues(board["risks"], limit=2)
        if issues:
            for risk in issues:
                lines.append(
                    f"  - [{str(risk.get('severity', 'low')).upper()}] "
                    f"{risk.get('message', 'No message')}"
                )
        else:
            lines.append("  - No issues detected")
        lines.append("")

    with open(path, "w", encoding="utf-8") as file:
        file.write("\n".join(lines))


def _write_project_html(path, summary, boards):
    board_cards = ""
    for index, board in enumerate(boards, start=1):
        health = _health_summary(board["score"], board["risks"])
        issues = _top_issues(board["risks"], limit=2)

        issue_html = ""
        if issues:
            for risk in issues:
                issue_html += (
                    f"<div class='mini-line'><strong>[{escape(str(risk.get('severity', 'low')).upper())}]</strong> "
                    f"{escape(str(risk.get('message', 'No message')))}</div>"
                )
        else:
            issue_html = "<div class='mini-line'>No issues detected.</div>"

        board_cards += f"""
        <section class="board-card">
            <div class="board-top">
                <div>
                    <div class="rank">#{index}</div>
                    <h2>{escape(board['filename'])}</h2>
                    <div class="subtle">{escape(health['title'])}</div>
                </div>
                <div class="score">{board['score']} / 10</div>
            </div>
            <p class="subtle">{escape(health['summary'])}</p>
            <div class="issue-block">
                <strong>Top Issues</strong>
                {issue_html}
            </div>
        </section>
        """

    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Silicore Project Summary</title>
    <style>
        body {{
            margin: 0;
            padding: 32px;
            background: #0b1020;
            color: #e8edf7;
            font-family: Arial, Helvetica, sans-serif;
        }}
        .page {{
            max-width: 1100px;
            margin: 0 auto;
        }}
        .hero, .board-card {{
            background: #141b2d;
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 18px;
            padding: 20px;
            margin-bottom: 18px;
        }}
        .hero h1 {{
            margin: 0 0 8px;
            font-size: 32px;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 12px;
            margin-top: 18px;
        }}
        .stat {{
            background: rgba(255,255,255,0.04);
            border-radius: 14px;
            padding: 14px;
        }}
        .stat-label {{
            font-size: 12px;
            text-transform: uppercase;
            color: #aab6d3;
            margin-bottom: 6px;
        }}
        .stat-value {{
            font-size: 28px;
            font-weight: bold;
        }}
        .board-top {{
            display: flex;
            justify-content: space-between;
            align-items: start;
            gap: 12px;
        }}
        .rank {{
            display: inline-block;
            padding: 6px 10px;
            border-radius: 999px;
            background: rgba(126,240,197,0.12);
            margin-bottom: 8px;
            font-size: 12px;
            font-weight: bold;
        }}
        .score {{
            font-size: 28px;
            font-weight: bold;
        }}
        .subtle {{
            color: #aab6d3;
        }}
        .mini-line {{
            margin-top: 8px;
        }}
        .issue-block {{
            margin-top: 12px;
            background: rgba(255,255,255,0.03);
            border-radius: 12px;
            padding: 12px 14px;
        }}
    </style>
</head>
<body>
    <div class="page">
        <section class="hero">
            <h1>Silicore Project Summary</h1>
            <div class="stats">
                <div class="stat">
                    <div class="stat-label">Boards</div>
                    <div class="stat-value">{summary['total_boards']}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Average</div>
                    <div class="stat-value">{summary['average_score']}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Best</div>
                    <div class="stat-value">{summary['best_score']}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Worst</div>
                    <div class="stat-value">{summary['worst_score']}</div>
                </div>
            </div>
        </section>

        {board_cards}
    </div>
</body>
</html>
"""

    with open(path, "w", encoding="utf-8") as file:
        file.write(html)


def _analyze_board_file(file_path, config):
    filename = os.path.basename(file_path)

    pcb = _load_board(file_path)
    pcb = _normalize_board(pcb)

    risks, _ = _run_rule_engine(pcb, config)
    score, score_explanation = _compute_score_and_explanation(risks, config)
    board_summary = _build_board_summary(pcb, risks, filename)

    return {
        "filename": filename,
        "score": score,
        "risks": risks,
        "score_explanation": score_explanation,
        "board_summary": board_summary,
    }


def run_single_analysis_from_path(file_path, config=None, output_dir="."):
    if config is None:
        config = load_config("custom_config.json")

    result = _analyze_board_file(file_path, config)

    os.makedirs(output_dir, exist_ok=True)

    json_path = os.path.join(output_dir, "single_analysis.json")
    report_md_path = os.path.join(output_dir, "single_report.md")
    report_html_path = os.path.join(output_dir, "single_report.html")

    _write_json(json_path, result)
    _write_single_markdown(report_md_path, result)
    _write_single_html(report_html_path, result)

    result["json_path"] = json_path
    result["report_md_path"] = report_md_path
    result["report_html_path"] = report_html_path

    return result


def analyze_project_directory(directory_path, config=None):
    if config is None:
        config = load_config("custom_config.json")

    board_files = []
    for name in sorted(os.listdir(directory_path)):
        full_path = os.path.join(directory_path, name)
        extension = os.path.splitext(name)[1].lower()
        if os.path.isfile(full_path) and extension in SUPPORTED_EXTENSIONS:
            board_files.append(full_path)

    if not board_files:
        raise ValueError("No supported board files were found in the provided directory.")

    boards = []
    for file_path in board_files:
        boards.append(_analyze_board_file(file_path, config))

    boards.sort(key=lambda item: item["score"], reverse=True)

    scores = [board["score"] for board in boards]
    summary = {
        "total_boards": len(boards),
        "average_score": round(sum(scores) / len(scores), 2) if scores else 0.0,
        "best_score": max(scores) if scores else 0.0,
        "worst_score": min(scores) if scores else 0.0,
    }

    output_dir = os.path.join(directory_path, "silicore_outputs")
    os.makedirs(output_dir, exist_ok=True)

    summary_json_path = os.path.join(output_dir, "project_summary.json")
    summary_md_path = os.path.join(output_dir, "project_summary.md")
    summary_html_path = os.path.join(output_dir, "project_summary.html")

    payload = {
        "summary": summary,
        "boards": boards,
    }

    _write_json(summary_json_path, payload)
    _write_project_markdown(summary_md_path, summary, boards)
    _write_project_html(summary_html_path, summary, boards)

    payload["summary_json_path"] = summary_json_path
    payload["summary_md_path"] = summary_md_path
    payload["summary_html_path"] = summary_html_path

    return payload


def analyze_single_board(uploaded_file, upload_folder, runs_folder, config_path):
    if uploaded_file is None or not uploaded_file.filename:
        raise ValueError("Please upload a board file.")

    extension = os.path.splitext(uploaded_file.filename)[1].lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError("Unsupported file type.")

    ensure_clean_upload_dir(upload_folder)
    ensure_runs_folder(runs_folder)

    filename = safe_filename(uploaded_file.filename)
    saved_path = os.path.join(upload_folder, filename)
    uploaded_file.save(saved_path)

    config = load_config(config_path)
    result = _analyze_board_file(saved_path, config)

    run_dir_name = create_run_directory(runs_folder)
    run_dir_path = os.path.join(runs_folder, run_dir_name)

    json_filename = "single_analysis.json"
    md_filename = "single_report.md"
    html_filename = "single_report.html"

    json_path = os.path.join(run_dir_path, json_filename)
    md_path = os.path.join(run_dir_path, md_filename)
    html_path = os.path.join(run_dir_path, html_filename)

    _write_json(json_path, result)
    _write_single_markdown(md_path, result)
    _write_single_html(html_path, result)

    result["downloads"] = build_single_downloads(run_dir_name)

    save_run_meta(
        run_dir_path,
        {
            "name": filename,
            "run_type": "single_board",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "score": result["score"],
        },
    )

    _, config_view = get_dashboard_config(config_path)

    return {
        "result": result,
        "config_view": config_view,
    }


def analyze_project_files(uploaded_files, upload_folder, runs_folder, config_path):
    valid_files = [file for file in uploaded_files if file and file.filename]
    if not valid_files:
        raise ValueError("Please upload at least one board file.")

    ensure_clean_upload_dir(upload_folder)
    ensure_runs_folder(runs_folder)

    config = load_config(config_path)
    saved_paths = []

    for uploaded_file in valid_files:
        extension = os.path.splitext(uploaded_file.filename)[1].lower()
        if extension not in SUPPORTED_EXTENSIONS:
            continue

        filename = safe_filename(uploaded_file.filename)
        saved_path = os.path.join(upload_folder, filename)
        uploaded_file.save(saved_path)
        saved_paths.append(saved_path)

    if not saved_paths:
        raise ValueError("No supported board files were uploaded.")

    boards = []
    for saved_path in saved_paths:
        boards.append(_analyze_board_file(saved_path, config))

    boards.sort(key=lambda item: item["score"], reverse=True)

    ranked_boards = []
    for index, board in enumerate(boards, start=1):
        board_copy = dict(board)
        board_copy["rank"] = index
        ranked_boards.append(board_copy)

    scores = [board["score"] for board in ranked_boards]
    project_summary = {
        "total_boards": len(ranked_boards),
        "average_score": round(sum(scores) / len(scores), 2) if scores else 0.0,
        "best_score": max(scores) if scores else 0.0,
        "worst_score": min(scores) if scores else 0.0,
    }

    run_dir_name = create_run_directory(runs_folder)
    run_dir_path = os.path.join(runs_folder, run_dir_name)

    summary_json_filename = "project_summary.json"
    summary_md_filename = "project_summary.md"
    summary_html_filename = "project_summary.html"

    summary_json_path = os.path.join(run_dir_path, summary_json_filename)
    summary_md_path = os.path.join(run_dir_path, summary_md_filename)
    summary_html_path = os.path.join(run_dir_path, summary_html_filename)

    payload = {
        "project_summary": project_summary,
        "boards": ranked_boards,
    }

    _write_json(summary_json_path, payload)
    _write_project_markdown(summary_md_path, project_summary, ranked_boards)
    _write_project_html(summary_html_path, project_summary, ranked_boards)

    payload["downloads"] = build_project_downloads(run_dir_name)

    save_run_meta(
        run_dir_path,
        {
            "name": "Project Analysis",
            "run_type": "project",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "score": project_summary["average_score"],
        },
    )

    _, config_view = get_dashboard_config(config_path)

    return {
        "project_result": payload,
        "config_view": config_view,
    }