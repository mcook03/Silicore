import importlib
import inspect
import json
import os
import shutil
from datetime import datetime, UTC
from html import escape

from engine.config_loader import load_config, get_editable_config_view, apply_analysis_profile
from engine.dashboard_storage import (
    ensure_runs_folder,
    create_run_directory,
    save_run_meta,
)

SUPPORTED_EXTENSIONS = {".txt", ".brd", ".kicad_pcb"}
FORMAT_READINESS = {
    ".kicad_pcb": {"label": "KiCad PCB", "status": "supported"},
    ".txt": {"label": "Structured Demo Text", "status": "supported"},
    ".brd": {"label": "Legacy Structured Board", "status": "supported"},
    ".gbr": {"label": "Gerber", "status": "planned"},
}


def _utc_now_iso():
    return datetime.now(UTC).isoformat()


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
        {"label": "Download Export Manifest", "url": f"/download/{run_dir_name}/export_manifest.json"},
    ]


def build_project_downloads(run_dir_name):
    return [
        {"label": "Download JSON", "url": f"/download/{run_dir_name}/project_summary.json"},
        {"label": "Download Markdown", "url": f"/download/{run_dir_name}/project_summary.md"},
        {"label": "Download HTML", "url": f"/download/{run_dir_name}/project_summary.html"},
        {"label": "Download Export Manifest", "url": f"/download/{run_dir_name}/export_manifest.json"},
    ]


def get_dashboard_config(config_path):
    config = load_config(config_path)
    return config, get_editable_config_view(config)


def _resolve_config(config):
    if config is None:
        return load_config("custom_config.json")

    if isinstance(config, str):
        return load_config(config)

    return config


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
        "confidence": risk.get("confidence", 0.8),
        "short_title": risk.get("short_title", risk.get("message", "No message provided.")),
        "fix_priority": risk.get("fix_priority", "medium"),
        "estimated_impact": risk.get("estimated_impact", "moderate"),
        "design_domain": risk.get("design_domain", "general"),
        "why_it_matters": risk.get("why_it_matters", ""),
        "suggested_actions": risk.get("suggested_actions", []),
        "trigger_condition": risk.get("trigger_condition", ""),
        "threshold_label": risk.get("threshold_label", ""),
        "observed_label": risk.get("observed_label", ""),
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


def _severity_rank(severity):
    order = {
        "critical": 4,
        "high": 3,
        "medium": 2,
        "low": 1,
    }
    return order.get(str(severity).lower(), 0)


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

    score_raw_10 = start_score - total_penalty
    score_raw_10 = max(min_score, min(max_score, score_raw_10))
    score_raw_10 = round(score_raw_10, 2)
    score_100 = round(score_raw_10 * 10, 1)

    return score_100, {
        "start_score": round(start_score * 10, 1),
        "start_score_raw_10": round(start_score, 2),
        "total_penalty": round(total_penalty * 10, 1),
        "total_penalty_raw_10": round(total_penalty, 2),
        "severity_totals": severity_totals,
        "category_totals": category_totals,
        "final_score": score_100,
        "final_score_raw_10": score_raw_10,
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
    category_counts = {}

    for risk in risks:
        severity = str(risk.get("severity", "unknown")).lower()
        category = str(risk.get("category", "unknown"))
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
        category_counts[category] = category_counts.get(category, 0) + 1

    component_refs = [_component_ref(component) for component in components[:10]]

    return {
        "filename": filename,
        "component_count": len(components),
        "net_count": len(nets),
        "sample_components": component_refs,
        "risk_count": len(risks),
        "severity_counts": severity_counts,
        "category_counts": category_counts,
    }


def _top_risks(risks, limit=3):
    ordered = sorted(
        risks,
        key=lambda risk: (
            _severity_rank(risk.get("severity")),
            len(str(risk.get("message", ""))),
        ),
        reverse=True,
    )
    return ordered[:limit]


def _category_label(category):
    return str(category).replace("_", " ").strip()


def _summarize_primary_category(risks):
    if not risks:
        return None

    category_counts = {}
    for risk in risks:
        category = str(risk.get("category", "unknown"))
        category_counts[category] = category_counts.get(category, 0) + 1

    if not category_counts:
        return None

    top_category = max(category_counts.items(), key=lambda item: item[1])[0]
    return _category_label(top_category)


def _score_band(score):
    if score > 10:
        score = score / 10.0
    if score >= 9.0:
        return "very low design risk"
    if score >= 7.0:
        return "moderate design risk"
    if score >= 4.0:
        return "elevated design risk"
    return "high design risk"


def _generate_executive_summary(result):
    score = float(result.get("score", 0))
    risks = result.get("risks", [])
    board_summary = result.get("board_summary", {})

    if not risks:
        return {
            "headline": "Board appears clean",
            "summary": (
                f"This board shows {_score_band(score)} with no detected rule violations. "
                "It appears structurally healthy under the current Silicore checks and is a stronger candidate for review or iteration."
            ),
            "top_issues": [],
        }

    primary_category = _summarize_primary_category(risks)
    top_risks = _top_risks(risks, limit=3)

    first_issue = top_risks[0]["message"] if top_risks else "No major issue identified."
    component_count = board_summary.get("component_count", 0)
    net_count = board_summary.get("net_count", 0)

    summary_parts = [
        f"This board shows {_score_band(score)}.",
    ]

    if primary_category:
        summary_parts.append(
            f"The main risk concentration is in {_category_label(primary_category)}."
        )

    summary_parts.append(f"The highest-priority issue is {first_issue}.")

    if component_count or net_count:
        summary_parts.append(
            f"The current design snapshot includes {component_count} components and {net_count} nets."
        )

    summary_parts.append(
        "The board is likely functional at a prototype level, but the highlighted issues should be addressed before stronger production confidence."
    )

    return {
        "headline": "Board needs focused engineering review",
        "summary": " ".join(summary_parts),
        "top_issues": [
            {
                "severity": risk.get("severity", "low"),
                "category": risk.get("category", "unknown"),
                "message": risk.get("message", "No message provided."),
                "recommendation": risk.get("recommendation", "Review this finding."),
            }
            for risk in top_risks
        ],
    }


def _generate_project_insight_summary(boards):
    if not boards:
        return {
            "headline": "No boards analyzed",
            "summary": "No supported board files were analyzed.",
            "best_board": None,
            "worst_board": None,
            "common_category": None,
        }

    ranked = sorted(boards, key=lambda board: board.get("score", 0), reverse=True)
    best_board = ranked[0]
    worst_board = ranked[-1]

    category_counts = {}
    for board in boards:
        for risk in board.get("risks", []):
            category = str(risk.get("category", "unknown"))
            category_counts[category] = category_counts.get(category, 0) + 1

    common_category = None
    if category_counts:
        common_category = max(category_counts.items(), key=lambda item: item[1])[0]

    spread = round(best_board.get("score", 0) - worst_board.get("score", 0), 2)

    summary = (
        f"The strongest board is {best_board.get('filename', 'unknown')} at {best_board.get('score', 0)} / 100, "
        f"while the weakest board is {worst_board.get('filename', 'unknown')} at {worst_board.get('score', 0)} / 100. "
        f"The current score spread across the project is {spread} points."
    )

    if common_category:
        summary += f" The most recurring issue area across the project is {_category_label(common_category)}."

    return {
        "headline": "Project comparison complete",
        "summary": summary,
        "best_board": {
            "filename": best_board.get("filename"),
            "score": best_board.get("score"),
        },
        "worst_board": {
            "filename": worst_board.get("filename"),
            "score": worst_board.get("score"),
        },
        "common_category": common_category,
    }


def _build_project_summary(boards):
    if not boards:
        return {
            "total_boards": 0,
            "average_score": 0.0,
            "best_score": 0.0,
            "worst_score": 0.0,
        }

    scores = [float(board.get("score", 0)) for board in boards]

    return {
        "total_boards": len(boards),
        "average_score": round(sum(scores) / len(scores), 2),
        "best_score": round(max(scores), 2),
        "worst_score": round(min(scores), 2),
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


def _format_confidence_display(confidence):
    value = confidence
    if value is None:
        return "Unknown"
    try:
        value = float(value)
    except (TypeError, ValueError):
        return str(confidence)
    if value <= 1.0:
        value *= 100
    return f"{round(value, 1)} / 100"


def _build_transparency_lines(risk):
    explanation = risk.get("explanation", {}) if isinstance(risk.get("explanation"), dict) else {}
    metrics = risk.get("metrics", {}) if isinstance(risk.get("metrics"), dict) else {}

    trigger = "A rule-based design condition triggered this finding."
    if str(risk.get("rule_id", "")).lower() == "spacing":
        trigger = "Component spacing dropped below the configured safe threshold."
    elif str(risk.get("rule_id", "")).lower() == "thermal":
        trigger = "Component proximity indicated likely thermal concentration."

    observed_parts = []
    if metrics.get("distance") is not None:
        observed_parts.append(f"distance={metrics.get('distance')}")
    if metrics.get("threshold") is not None:
        observed_parts.append(f"threshold={metrics.get('threshold')}")

    return {
        "trigger": trigger,
        "observed": ", ".join(observed_parts) if observed_parts else "No measured value preserved.",
        "reasoning": explanation.get("root_cause", "General design issue"),
        "impact": explanation.get("impact", "Unknown system impact"),
        "confidence": _format_confidence_display(explanation.get("confidence")),
    }


def _write_export_manifest(path, *, run_type, title, files, supported_formats, notes):
    payload = {
        "run_type": run_type,
        "title": title,
        "generated_at": _utc_now_iso(),
        "artifacts": files,
        "parser_capabilities": supported_formats,
        "notes": notes,
    }
    _write_json(path, payload)


def _write_single_markdown(path, result):
    executive_summary = result.get("executive_summary", {})
    board_summary = result.get("board_summary", {})
    severity_totals = result["score_explanation"].get("severity_totals", {})
    category_totals = result["score_explanation"].get("category_totals", {})

    lines = [
        "# SILICORE ENGINEERING REPORT",
        "",
        f"- File: {result['filename']}",
        f"- Score: {result['score']} / 100",
        f"- Total Risks: {len(result['risks'])}",
        f"- Total Penalty: {result['score_explanation'].get('total_penalty', 0)}",
        "",
        "## Executive Summary",
        "",
        f"**{executive_summary.get('headline', 'Board review summary')}**",
        "",
        executive_summary.get("summary", "No summary available."),
        "",
        "## Parser Capability",
        "",
        "- Current production-ready inputs: `.kicad_pcb`, `.txt`",
        "- Planned next-stage inputs: Altium-style board imports, Gerber-derived review flows",
        "",
    ]

    top_issues = executive_summary.get("top_issues", [])
    if top_issues:
        lines.extend(["## Top Issues", ""])
        for index, issue in enumerate(top_issues, start=1):
            lines.append(
                f"{index}. **{str(issue.get('severity', 'low')).upper()}** — "
                f"{issue.get('category', 'unknown')} — {issue.get('message', 'No message provided.')}"
            )
            lines.append(f"   - Recommendation: {issue.get('recommendation', 'Review this finding.')}")
        lines.append("")

    lines.extend(["## Board Summary", ""])
    if board_summary:
        lines.append(f"- Component Count: {board_summary.get('component_count', 0)}")
        lines.append(f"- Net Count: {board_summary.get('net_count', 0)}")
        lines.append(f"- Risk Count: {board_summary.get('risk_count', 0)}")
        lines.append(f"- Sample Components: {', '.join(board_summary.get('sample_components', []))}")
    else:
        lines.append("- No board summary available")

    lines.extend(["", "## Severity Penalties", ""])
    if severity_totals:
        for severity, value in severity_totals.items():
            lines.append(f"- {severity}: {value}")
    else:
        lines.append("- None")

    lines.extend(["", "## Category Penalties", ""])
    if category_totals:
        for category, value in category_totals.items():
            lines.append(f"- {category}: {value}")
    else:
        lines.append("- None")

    lines.extend(["", "## Detailed Findings", ""])
    if result["risks"]:
        for risk in result["risks"]:
            lines.append(f"### {risk['severity'].upper()} — {risk['category']}")
            lines.append(f"- Message: {risk['message']}")
            lines.append(f"- Recommendation: {risk['recommendation']}")

            explanation = risk.get("explanation", {})
            if explanation:
                lines.append(f"- Root Cause: {explanation.get('root_cause', 'Unknown')}")
                lines.append(f"- Impact: {explanation.get('impact', 'Unknown')}")
                lines.append(f"- Confidence: {explanation.get('confidence', 'Unknown')}")

            transparency = _build_transparency_lines(risk)
            lines.append(f"- Trigger Condition: {transparency['trigger']}")
            lines.append(f"- Observed vs Threshold: {transparency['observed']}")
            lines.append(f"- Engineering Impact: {transparency['impact']}")
            lines.append(f"- Trust Confidence: {transparency['confidence']}")

            fix_suggestion = risk.get("fix_suggestion", {})
            if fix_suggestion:
                lines.append(f"- Suggested Fix: {fix_suggestion.get('fix', 'Manual review required')}")
                lines.append(f"- Fix Priority: {fix_suggestion.get('priority', 'medium')}")

            if risk.get("components"):
                lines.append(f"- Components: {', '.join(risk['components'])}")

            if risk.get("nets"):
                lines.append(f"- Nets: {', '.join(risk['nets'])}")

            if risk.get("metrics"):
                lines.append(f"- Metrics: {json.dumps(risk['metrics'])}")

            lines.append("")
    else:
        lines.append("No risks detected.")

    with open(path, "w", encoding="utf-8") as file:
        file.write("\n".join(lines))


def _write_single_html(path, result):
    executive_summary = result.get("executive_summary", {})
    board_summary = result.get("board_summary", {})
    top_issues = executive_summary.get("top_issues", [])

    top_issues_html = ""
    if top_issues:
        for issue in top_issues:
            top_issues_html += f"""
            <div class="issue-card">
                <p><strong>{escape(str(issue.get('severity', 'low')).upper())}</strong> — {escape(str(issue.get('category', 'unknown')))}</p>
                <p>{escape(str(issue.get('message', 'No message provided.')))}</p>
                <p><strong>Recommendation:</strong> {escape(str(issue.get('recommendation', 'Review this finding.')))}</p>
            </div>
            """
    else:
        top_issues_html = "<p>No priority issues identified.</p>"

    risks_html = ""
    if result["risks"]:
        for risk in result["risks"]:
            components_html = ""
            nets_html = ""
            metrics_html = ""
            explanation_html = ""
            fix_html = ""

            if risk.get("components"):
                components_html = f"<p><strong>Components:</strong> {escape(', '.join(risk['components']))}</p>"

            if risk.get("nets"):
                nets_html = f"<p><strong>Nets:</strong> {escape(', '.join(risk['nets']))}</p>"

            if risk.get("metrics"):
                metrics_html = f"<p><strong>Metrics:</strong> {escape(json.dumps(risk['metrics']))}</p>"

            explanation = risk.get("explanation", {})
            if explanation:
                explanation_html = f"""
                <p><strong>Root Cause:</strong> {escape(str(explanation.get('root_cause', 'Unknown')))}</p>
                <p><strong>Impact:</strong> {escape(str(explanation.get('impact', 'Unknown')))}</p>
                <p><strong>Confidence:</strong> {escape(_format_confidence_display(explanation.get('confidence')))}</p>
                """

            fix_suggestion = risk.get("fix_suggestion", {})
            if fix_suggestion:
                fix_html = f"""
                <p><strong>Suggested Fix:</strong> {escape(str(fix_suggestion.get('fix', 'Manual review required')))}</p>
                <p><strong>Fix Priority:</strong> {escape(str(fix_suggestion.get('priority', 'medium')))}</p>
                """

            transparency = _build_transparency_lines(risk)

            risks_html += f"""
            <div class="risk-card">
                <p><strong>Severity:</strong> {escape(str(risk['severity']))}</p>
                <p><strong>Category:</strong> {escape(str(risk['category']))}</p>
                <p><strong>Message:</strong> {escape(str(risk['message']))}</p>
                <p><strong>Recommendation:</strong> {escape(str(risk['recommendation']))}</p>
                <p><strong>Trigger Condition:</strong> {escape(str(transparency['trigger']))}</p>
                <p><strong>Observed vs Threshold:</strong> {escape(str(transparency['observed']))}</p>
                <p><strong>Engineering Impact:</strong> {escape(str(transparency['impact']))}</p>
                <p><strong>Trust Confidence:</strong> {escape(str(transparency['confidence']))}</p>
                {explanation_html}
                {fix_html}
                {components_html}
                {nets_html}
                {metrics_html}
            </div>
            """
    else:
        risks_html = "<p>No risks detected.</p>"

    severity_items = ""
    for severity, value in result["score_explanation"].get("severity_totals", {}).items():
        severity_items += f"<li>{escape(str(severity))}: {value}</li>"
    if not severity_items:
        severity_items = "<li>None</li>"

    category_items = ""
    for category, value in result["score_explanation"].get("category_totals", {}).items():
        category_items += f"<li>{escape(str(category))}: {value}</li>"
    if not category_items:
        category_items = "<li>None</li>"

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Silicore Engineering Report</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                background: #0f172a;
                color: #e2e8f0;
            }}
            .container {{
                max-width: 1100px;
                margin: 0 auto;
                padding: 32px 20px 60px;
            }}
            .hero {{
                background: linear-gradient(135deg, #111827, #1e293b);
                border: 1px solid #334155;
                border-radius: 18px;
                padding: 24px;
                margin-bottom: 20px;
            }}
            .card {{
                background: #111827;
                border: 1px solid #334155;
                border-radius: 16px;
                padding: 20px;
                margin-bottom: 20px;
            }}
            .issue-card, .risk-card {{
                background: #1e293b;
                border: 1px solid #475569;
                border-radius: 12px;
                padding: 14px;
                margin-bottom: 12px;
            }}
            h1, h2, h3 {{
                margin-top: 0;
            }}
            ul {{
                padding-left: 20px;
            }}
            .muted {{
                color: #cbd5e1;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="hero">
                <h1>Silicore Engineering Report</h1>
                <p><strong>File:</strong> {escape(result['filename'])}</p>
                <p><strong>Score:</strong> {result['score']} / 100</p>
                <p><strong>Total Risks:</strong> {len(result['risks'])}</p>
                <p><strong>Total Penalty:</strong> {result['score_explanation'].get('total_penalty', 0)}</p>
            </div>

            <div class="card">
                <h2>Executive Summary</h2>
                <p><strong>{escape(str(executive_summary.get('headline', 'Board review summary')))}</strong></p>
                <p class="muted">{escape(str(executive_summary.get('summary', 'No summary available.')))}</p>
            </div>

            <div class="card">
                <h2>Parser Capability</h2>
                <p><strong>Current production-ready inputs:</strong> .kicad_pcb, .txt</p>
                <p><strong>Planned next-stage inputs:</strong> Altium-style board imports, Gerber-derived review flows</p>
            </div>

            <div class="card">
                <h2>Top Issues</h2>
                {top_issues_html}
            </div>

            <div class="card">
                <h2>Board Summary</h2>
                <p><strong>Component Count:</strong> {board_summary.get('component_count', 0)}</p>
                <p><strong>Net Count:</strong> {board_summary.get('net_count', 0)}</p>
                <p><strong>Risk Count:</strong> {board_summary.get('risk_count', 0)}</p>
                <p><strong>Sample Components:</strong> {escape(', '.join(board_summary.get('sample_components', [])))}</p>
            </div>

            <div class="card">
                <h2>Severity Penalties</h2>
                <ul>{severity_items}</ul>
            </div>

            <div class="card">
                <h2>Category Penalties</h2>
                <ul>{category_items}</ul>
            </div>

            <div class="card">
                <h2>Detailed Findings</h2>
                {risks_html}
            </div>
        </div>
    </body>
    </html>
    """

    with open(path, "w", encoding="utf-8") as file:
        file.write(html)


def _write_project_markdown(path, project_data):
    project_summary = project_data.get("summary", {})
    project_insight = project_data.get("project_insight", {})
    boards = project_data.get("boards", [])

    lines = [
        "# SILICORE PROJECT SUMMARY",
        "",
        f"- Total Boards: {project_summary.get('total_boards', 0)}",
        f"- Average Score: {project_summary.get('average_score', 0.0)} / 100",
        f"- Best Score: {project_summary.get('best_score', 0.0)} / 100",
        f"- Worst Score: {project_summary.get('worst_score', 0.0)} / 100",
        "",
    ]

    if project_insight:
        lines.extend([
            "## Project Insight",
            "",
            f"**{project_insight.get('headline', 'Project review summary')}**",
            "",
            project_insight.get("summary", "No project insight available."),
            "",
        ])

    lines.extend([
        "## Parser Capability",
        "",
        "- Current production-ready inputs: `.kicad_pcb`, `.txt`",
        "- Planned next-stage inputs: Altium-style board imports, Gerber-derived review flows",
        "",
    ])

    lines.extend(["## Ranked Boards", ""])

    if boards:
        for board in boards:
            lines.append(f"### #{board.get('rank', '?')} — {board.get('filename', 'Unknown')}")
            lines.append(f"- Score: {board.get('score', 0)} / 100")
            lines.append(f"- Total Risks: {len(board.get('risks', []))}")
            lines.append(f"- Total Penalty: {board.get('score_explanation', {}).get('total_penalty', 0)}")
            if board.get("executive_summary", {}).get("summary"):
                lines.append(f"- Summary: {board['executive_summary']['summary']}")
            top_risks = board.get("risks", [])[:3]
            for risk in top_risks:
                transparency = _build_transparency_lines(risk)
                lines.append(f"  - Finding: {risk.get('message', 'No message')}")
                lines.append(f"    - Trigger: {transparency['trigger']}")
                lines.append(f"    - Observed: {transparency['observed']}")
                lines.append(f"    - Confidence: {transparency['confidence']}")
            lines.append("")
    else:
        lines.append("No boards analyzed.")

    with open(path, "w", encoding="utf-8") as file:
        file.write("\n".join(lines))


def _write_project_html(path, project_data):
    project_summary = project_data.get("summary", {})
    project_insight = project_data.get("project_insight", {})
    boards = project_data.get("boards", [])

    boards_html = ""
    if boards:
        for board in boards:
            boards_html += f"""
            <div class="board-card">
                <h3>#{board.get('rank', '?')} — {escape(str(board.get('filename', 'Unknown')))}</h3>
                <p><strong>Score:</strong> {board.get('score', 0)} / 100</p>
                <p><strong>Total Risks:</strong> {len(board.get('risks', []))}</p>
                <p><strong>Total Penalty:</strong> {board.get('score_explanation', {}).get('total_penalty', 0)}</p>
                <p>{escape(str(board.get('executive_summary', {}).get('summary', 'No summary available.')))}</p>
            </div>
            """
    else:
        boards_html = "<p>No boards analyzed.</p>"

    insight_html = ""
    if project_insight:
        insight_html = f"""
        <div class="hero">
            <p><strong>{escape(str(project_insight.get('headline', 'Project review summary')))}</strong></p>
            <p>{escape(str(project_insight.get('summary', 'No project insight available.')))}</p>
        </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Silicore Project Summary</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                background: #0f172a;
                color: #e2e8f0;
            }}
            .container {{
                max-width: 1100px;
                margin: 0 auto;
                padding: 32px 20px 60px;
            }}
            .hero {{
                background: linear-gradient(135deg, #111827, #1e293b);
                border: 1px solid #334155;
                border-radius: 18px;
                padding: 24px;
                margin-bottom: 20px;
            }}
            .board-card {{
                background: #111827;
                border: 1px solid #334155;
                border-radius: 16px;
                padding: 18px;
                margin-bottom: 16px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="hero">
                <h1>Silicore Project Summary</h1>
                <p><strong>Total Boards:</strong> {project_summary.get('total_boards', 0)}</p>
                <p><strong>Average Score:</strong> {project_summary.get('average_score', 0.0)} / 100</p>
                <p><strong>Best Score:</strong> {project_summary.get('best_score', 0.0)} / 100</p>
                <p><strong>Worst Score:</strong> {project_summary.get('worst_score', 0.0)} / 100</p>
            </div>

            {insight_html}

            <div class="hero">
                <p><strong>Parser Capability</strong></p>
                <p>Current production-ready inputs: .kicad_pcb, .txt</p>
                <p>Planned next-stage inputs: Altium-style board imports, Gerber-derived review flows</p>
            </div>

            {boards_html}
        </div>
    </body>
    </html>
    """

    with open(path, "w", encoding="utf-8") as file:
        file.write(html)


def _risk_base_signature(risk):
    category = str(risk.get("category", "")).strip()
    message = str(risk.get("message", "")).strip()
    return f"{category}|{message}"


def _risk_signature(risk):
    severity = str(risk.get("severity", "")).lower().strip()
    return f"{severity}|{_risk_base_signature(risk)}"


def _build_risk_snapshot(risks):
    snapshot = []

    for risk in risks or []:
        snapshot.append(
            {
                "base_signature": _risk_base_signature(risk),
                "signature": _risk_signature(risk),
                "severity": str(risk.get("severity", "low")).lower(),
                "category": str(risk.get("category", "unknown")),
                "message": risk.get("message", "No message provided."),
                "recommendation": risk.get("recommendation", "Review this finding."),
                "components": risk.get("components", []),
                "nets": risk.get("nets", []),
                "metrics": risk.get("metrics", {}),
                "confidence": risk.get("confidence", 0.8),
                "design_domain": risk.get("design_domain", "general"),
                "why_it_matters": risk.get("why_it_matters", ""),
                "trigger_condition": risk.get("trigger_condition", ""),
                "threshold_label": risk.get("threshold_label", ""),
                "observed_label": risk.get("observed_label", ""),
            }
        )

    return snapshot


def _build_category_summary_from_risks(risks):
    categories = {}
    for risk in risks or []:
        category = str(risk.get("category", "unknown"))
        categories[category] = categories.get(category, 0) + 1
    return categories


def _build_run_record(result, run_dir_name, run_type):
    risks = result.get("risks", []) or []
    analysis_context = result.get("analysis_context", {}) or {}

    return {
        "run_id": run_dir_name,
        "name": result.get("filename"),
        "run_type": run_type,
        "created_at": _utc_now_iso(),
        "score": result.get("score"),
        "risk_count": len(risks),
        "critical_count": sum(
            1 for risk in risks if str(risk.get("severity", "")).lower() == "critical"
        ),
        "summary": result.get("executive_summary", {}).get("summary"),
        "path": run_dir_name,
        "analysis_context": analysis_context,
        "config_snapshot": result.get("config_snapshot", {}),
        "risk_snapshot": _build_risk_snapshot(risks),
        "category_summary": _build_category_summary_from_risks(risks),
    }


def _build_project_run_record(project_result, run_dir_name, saved_names):
    boards = project_result.get("boards", []) or []
    all_risks = []

    for board in boards:
        all_risks.extend(board.get("risks", []) or [])

    display_name = ", ".join(saved_names[:3])
    if len(saved_names) > 3:
        display_name += "..."

    return {
        "run_id": run_dir_name,
        "name": display_name,
        "run_type": "project",
        "created_at": _utc_now_iso(),
        "score": project_result.get("summary", {}).get("average_score"),
        "risk_count": len(all_risks),
        "critical_count": sum(
            1 for risk in all_risks if str(risk.get("severity", "")).lower() == "critical"
        ),
        "summary": project_result.get("project_insight", {}).get("summary"),
        "path": run_dir_name,
        "analysis_context": project_result.get("analysis_context", {}),
        "config_snapshot": project_result.get("config_snapshot", {}),
        "risk_snapshot": _build_risk_snapshot(all_risks),
        "category_summary": _build_category_summary_from_risks(all_risks),
    }


def _analyze_board_file(file_path, config):
    pcb = _load_board(file_path)
    pcb = _normalize_board(pcb)

    risks, raw_rule_result = _run_rule_engine(pcb, config)
    score, score_explanation = _compute_score_and_explanation(risks, config)
    board_summary = _build_board_summary(pcb, risks, os.path.basename(file_path))

    result = {
        "filename": os.path.basename(file_path),
        "file_path": file_path,
        "score": score,
        "risks": risks,
        "score_explanation": score_explanation,
        "board_summary": board_summary,
        "pcb_snapshot": pcb.to_dict() if hasattr(pcb, "to_dict") else {},
        "config_snapshot": config,
        "analysis_context": {
            "board_name": os.path.basename(file_path),
            "timestamp": _utc_now_iso(),
            "config_snapshot": config,
            "profile": (config.get("analysis", {}) or {}).get("profile", "balanced"),
            "board_type": (config.get("analysis", {}) or {}).get("board_type", "general"),
        },
        "raw_rule_result": raw_rule_result,
        "generated_at": _utc_now_iso(),
    }

    result["executive_summary"] = _generate_executive_summary(result)
    return result


def run_single_analysis_from_path(file_path, config=None, output_dir=None, profile_name=None, board_type=None):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Board file not found: {file_path}")

    extension = os.path.splitext(file_path)[1].lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {extension}")

    config = apply_analysis_profile(_resolve_config(config), profile_name=profile_name, board_type=board_type)

    result = _analyze_board_file(file_path, config)

    if output_dir is not None:
        os.makedirs(output_dir, exist_ok=True)
        json_path = os.path.join(output_dir, "single_analysis.json")
        md_path = os.path.join(output_dir, "single_report.md")
        html_path = os.path.join(output_dir, "single_report.html")
    else:
        base_dir = os.path.dirname(file_path) or "."
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        json_path = os.path.join(base_dir, f"{base_name}_analysis.json")
        md_path = os.path.join(base_dir, f"{base_name}_report.md")
        html_path = os.path.join(base_dir, f"{base_name}_report.html")

    _write_json(json_path, result)
    _write_single_markdown(md_path, result)
    _write_single_html(html_path, result)
    if output_dir is not None:
        manifest_path = os.path.join(output_dir, "export_manifest.json")
        _write_export_manifest(
            manifest_path,
            run_type="single",
            title=result.get("filename", "Single Board Analysis"),
            files=[
                {"name": os.path.basename(json_path), "kind": "json"},
                {"name": os.path.basename(md_path), "kind": "markdown"},
                {"name": os.path.basename(html_path), "kind": "html"},
            ],
            supported_formats=FORMAT_READINESS,
            notes=["Artifacts include structured analysis, engineering summary, and print-friendly HTML."],
        )

    result["json_path"] = json_path
    result["report_md_path"] = md_path
    result["report_html_path"] = html_path
    result["markdown_path"] = md_path
    result["html_path"] = html_path
    if output_dir is not None:
        result["manifest_path"] = os.path.join(output_dir, "export_manifest.json")

    return result


def analyze_project_paths(file_paths, config=None, output_dir=None, profile_name=None, board_type=None):
    config = apply_analysis_profile(_resolve_config(config), profile_name=profile_name, board_type=board_type)

    boards = []
    for file_path in file_paths:
        board_result = _analyze_board_file(file_path, config)
        boards.append(board_result)

    boards = sorted(boards, key=lambda board: board.get("score", 0), reverse=True)

    for index, board in enumerate(boards, start=1):
        board["rank"] = index

    summary = _build_project_summary(boards)
    project_insight = _generate_project_insight_summary(boards)

    project_data = {
        "generated_at": _utc_now_iso(),
        "summary": summary,
        "project_insight": project_insight,
        "boards": boards,
        "config_snapshot": config,
        "analysis_context": {
            "board_name": "Project Analysis",
            "timestamp": _utc_now_iso(),
            "config_snapshot": config,
            "profile": (config.get("analysis", {}) or {}).get("profile", "balanced"),
            "board_type": (config.get("analysis", {}) or {}).get("board_type", "general"),
        },
    }

    summary_json_path = None
    summary_md_path = None
    summary_html_path = None

    if output_dir is not None:
        os.makedirs(output_dir, exist_ok=True)

        summary_json_path = os.path.join(output_dir, "project_summary.json")
        summary_md_path = os.path.join(output_dir, "project_summary.md")
        summary_html_path = os.path.join(output_dir, "project_summary.html")

        _write_json(summary_json_path, project_data)
        _write_project_markdown(summary_md_path, project_data)
        _write_project_html(summary_html_path, project_data)
        _write_export_manifest(
            os.path.join(output_dir, "export_manifest.json"),
            run_type="project",
            title="Project Review Export",
            files=[
                {"name": os.path.basename(summary_json_path), "kind": "json"},
                {"name": os.path.basename(summary_md_path), "kind": "markdown"},
                {"name": os.path.basename(summary_html_path), "kind": "html"},
            ],
            supported_formats=FORMAT_READINESS,
            notes=["Artifacts include project summary, ranked boards, and transparency-enriched review output."],
        )

    return {
        "boards": boards,
        "summary": summary,
        "project_insight": project_insight,
        "summary_json_path": summary_json_path,
        "summary_md_path": summary_md_path,
        "summary_html_path": summary_html_path,
    }


def analyze_project_directory(directory_path, config=None):
    if not os.path.isdir(directory_path):
        raise FileNotFoundError(f"Directory not found: {directory_path}")

    file_paths = []
    for name in sorted(os.listdir(directory_path)):
        full_path = os.path.join(directory_path, name)
        if not os.path.isfile(full_path):
            continue

        extension = os.path.splitext(name)[1].lower()
        if extension in SUPPORTED_EXTENSIONS:
            file_paths.append(full_path)

    if not file_paths:
        return {
            "boards": [],
            "summary": _build_project_summary([]),
            "project_insight": _generate_project_insight_summary([]),
            "summary_json_path": None,
            "summary_md_path": None,
            "summary_html_path": None,
        }

    output_dir = os.path.join(directory_path, "silicore_outputs")
    os.makedirs(output_dir, exist_ok=True)

    return analyze_project_paths(file_paths, config=config, output_dir=output_dir)


def analyze_single_board(uploaded_file, upload_folder, runs_folder, config_path, profile_name=None, board_type=None):
    if uploaded_file is None or not getattr(uploaded_file, "filename", ""):
        raise ValueError("Please upload a board file first.")

    filename = safe_filename(uploaded_file.filename)
    extension = os.path.splitext(filename)[1].lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError("Unsupported file type. Use .txt, .brd, or .kicad_pcb.")

    ensure_clean_upload_dir(upload_folder)
    ensure_runs_folder(runs_folder)

    file_path = os.path.join(upload_folder, filename)
    uploaded_file.save(file_path)

    base_config, config_view = get_dashboard_config(config_path)
    config = apply_analysis_profile(base_config, profile_name=profile_name, board_type=board_type)

    run_dir_name, run_dir = create_run_directory("single", runs_folder)

    result = run_single_analysis_from_path(
        file_path=file_path,
        config=config,
        output_dir=run_dir,
        profile_name=profile_name,
        board_type=board_type,
    )

    result["downloads"] = build_single_downloads(run_dir_name)

    save_run_meta(
        run_dir,
        {
            "name": filename,
            "run_type": "single",
            "created_at": _utc_now_iso(),
            "filename": filename,
            "score": result.get("score"),
        },
    )

    run_record = _build_run_record(result, run_dir_name, "single")

    return {
        "config": config,
        "config_view": config_view,
        "result": result,
        "run_record": run_record,
    }


def analyze_project_files(uploaded_files, upload_folder, runs_folder, config_path, profile_name=None, board_type=None):
    files = [file for file in uploaded_files if file and getattr(file, "filename", "").strip()]
    if not files:
        raise ValueError("Please upload at least one board file.")

    ensure_clean_upload_dir(upload_folder)
    ensure_runs_folder(runs_folder)

    saved_paths = []
    saved_names = []

    for uploaded_file in files:
        filename = safe_filename(uploaded_file.filename)
        extension = os.path.splitext(filename)[1].lower()

        if extension not in SUPPORTED_EXTENSIONS:
            continue

        file_path = os.path.join(upload_folder, filename)
        uploaded_file.save(file_path)
        saved_paths.append(file_path)
        saved_names.append(filename)

    if not saved_paths:
        raise ValueError("No supported board files were uploaded.")

    base_config, config_view = get_dashboard_config(config_path)
    config = apply_analysis_profile(base_config, profile_name=profile_name, board_type=board_type)

    run_dir_name, run_dir = create_run_directory("project", runs_folder)

    project_result = analyze_project_paths(
        file_paths=saved_paths,
        config=config,
        output_dir=run_dir,
        profile_name=profile_name,
        board_type=board_type,
    )

    project_result["downloads"] = build_project_downloads(run_dir_name)

    save_run_meta(
        run_dir,
        {
            "name": ", ".join(saved_names[:3]) + ("..." if len(saved_names) > 3 else ""),
            "run_type": "project",
            "created_at": _utc_now_iso(),
            "board_count": len(saved_paths),
        },
    )

    run_record = _build_project_run_record(project_result, run_dir_name, saved_names)

    return {
        "config": config,
        "config_view": config_view,
        "project_result": project_result,
        "run_record": run_record,
    }
