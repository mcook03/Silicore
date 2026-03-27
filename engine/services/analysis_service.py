import importlib
import inspect
import json
import os
import shutil
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
        ["explain_risk"]
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
        ["suggest_fix"]
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
    return config.get("score", {}).get("severity_penalties", {
        "low": 0.5,
        "medium": 1.0,
        "high": 1.5,
        "critical": 2.0
    })


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
        severity_totals[severity] = round(
            severity_totals.get(severity, 0.0) + penalty, 2
        )
        category_totals[category] = round(
            category_totals.get(category, 0.0) + penalty, 2
        )

        details.append({
            "severity": severity,
            "category": category,
            "penalty": penalty,
            "message": risk.get("message", ""),
            "root_cause": risk.get("explanation", {}).get("root_cause", ""),
            "impact": risk.get("explanation", {}).get("impact", ""),
            "confidence": risk.get("explanation", {}).get("confidence"),
            "suggested_fix": risk.get("fix_suggestion", {}).get("fix", ""),
            "fix_priority": risk.get("fix_suggestion", {}).get("priority", ""),
        })

    score = start_score - total_penalty
    score = max(min_score, min(max_score, score))
    score = round(score, 2)

    return score, {
        "start_score": start_score,
        "total_penalty": round(total_penalty, 2),
        "severity_totals": severity_totals,
        "category_totals": category_totals,
        "details": details
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
        return component.get("ref") or component.get("reference") or component.get("name") or "UNKNOWN"
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
        "severity_counts": severity_counts
    }


def _load_board(file_path):
    extension = os.path.splitext(file_path)[1].lower()

    if extension == ".kicad_pcb":
        parser_func = _optional_function(
            "engine.kicad_parser",
            ["parse_kicad_pcb", "parse_kicad_file", "parse_board"]
        )
        if parser_func:
            return _call_with_supported_args(
                parser_func,
                file_path=file_path,
                path=file_path,
                filename=file_path
            )

    parser_func = _optional_function(
        "engine.parser",
        ["parse_pcb_file", "parse_file", "load_pcb", "parse_board"]
    )
    if parser_func:
        return _call_with_supported_args(
            parser_func,
            file_path=file_path,
            path=file_path,
            filename=file_path
        )

    raise RuntimeError("No compatible board parser was found.")


def _normalize_board(pcb):
    normalize_func = _optional_function(
        "engine.normalizer",
        ["normalize_pcb", "normalize_board"]
    )

    if not normalize_func:
        return pcb

    try:
        normalized = _call_with_supported_args(
            normalize_func,
            pcb=pcb,
            board=pcb
        )
        return normalized if normalized is not None else pcb
    except Exception:
        return pcb


def _run_rule_engine(pcb, config):
    rule_func = _optional_function(
        "engine.rule_runner",
        ["run_analysis", "run_rule_engine", "run_rules"]
    )

    if not rule_func:
        raise RuntimeError("No compatible rule runner was found.")

    result = _call_with_supported_args(
        rule_func,
        pcb=pcb,
        board=pcb,
        config=config
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
    lines = [
        "# SILICORE ENGINEERING REPORT",
        "",
        f"- File: {result['filename']}",
        f"- Score: {result['score']} / 10",
        f"- Total Risks: {len(result['risks'])}",
        f"- Total Penalty: {result['score_explanation'].get('total_penalty', 0)}",
        "",
        "## Board Summary",
        ""
    ]

    board_summary = result.get("board_summary", {})
    if board_summary:
        lines.append(f"- Component Count: {board_summary.get('component_count', 0)}")
        lines.append(f"- Net Count: {board_summary.get('net_count', 0)}")
        lines.append(f"- Risk Count: {board_summary.get('risk_count', 0)}")
        lines.append(f"- Sample Components: {', '.join(board_summary.get('sample_components', []))}")
    else:
        lines.append("- No board summary available")

    lines.extend([
        "",
        "## Severity Penalties",
        ""
    ])

    severity_totals = result["score_explanation"].get("severity_totals", {})
    if severity_totals:
        for severity, value in severity_totals.items():
            lines.append(f"- {severity}: {value}")
    else:
        lines.append("- None")

    lines.extend([
        "",
        "## Category Penalties",
        ""
    ])

    category_totals = result["score_explanation"].get("category_totals", {})
    if category_totals:
        for category, value in category_totals.items():
            lines.append(f"- {category}: {value}")
    else:
        lines.append("- None")

    lines.extend([
        "",
        "## Detailed Findings",
        ""
    ])

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

            fix_suggestion = risk.get("fix_suggestion", {})
            if fix_suggestion:
                lines.append(f"- Suggested Fix: {fix_suggestion.get('fix', 'Manual review required')}")
                lines.append(f"- Fix Priority: {fix_suggestion.get('priority', 'medium')}")

            if risk.get("components"):
                lines.append(f"- Components: {', '.join(risk['components'])}")
            if risk.get("nets"):
                lines.append(f"- Nets: {', '.join(risk['nets'])}")
            lines.append("")
    else:
        lines.append("No risks detected.")

    with open(path, "w", encoding="utf-8") as file:
        file.write("\n".join(lines))


def _write_single_html(path, result):
    risks_html = ""

    if result["risks"]:
        for risk in result["risks"]:
            components_html = ""
            nets_html = ""
            explanation_html = ""
            fix_html = ""

            if risk.get("components"):
                components_html = f"<p><strong>Components:</strong> {escape(', '.join(risk['components']))}</p>"
            if risk.get("nets"):
                nets_html = f"<p><strong>Nets:</strong> {escape(', '.join(risk['nets']))}</p>"

            explanation = risk.get("explanation", {})
            if explanation:
                explanation_html = f"""
                <p><strong>Root Cause:</strong> {escape(str(explanation.get('root_cause', 'Unknown')))}</p>
                <p><strong>Impact:</strong> {escape(str(explanation.get('impact', 'Unknown')))}</p>
                <p><strong>Confidence:</strong> {escape(str(explanation.get('confidence', 'Unknown')))}</p>
                """

            fix_suggestion = risk.get("fix_suggestion", {})
            if fix_suggestion:
                fix_html = f"""
                <p><strong>Suggested Fix:</strong> {escape(str(fix_suggestion.get('fix', 'Manual review required')))}</p>
                <p><strong>Fix Priority:</strong> {escape(str(fix_suggestion.get('priority', 'medium')))}</p>
                """

            risks_html += f"""
            <div class="risk">
                <p><strong>Severity:</strong> {escape(str(risk['severity']))}</p>
                <p><strong>Category:</strong> {escape(str(risk['category']))}</p>
                <p><strong>Message:</strong> {escape(str(risk['message']))}</p>
                <p><strong>Recommendation:</strong> {escape(str(risk['recommendation']))}</p>
                {explanation_html}
                {fix_html}
                {components_html}
                {nets_html}
            </div>
            """
    else:
        risks_html = "<p>No risks detected.</p>"

    board_summary = result.get("board_summary", {})
    board_summary_html = f"""
        <p><strong>Component Count:</strong> {board_summary.get('component_count', 0)}</p>
        <p><strong>Net Count:</strong> {board_summary.get('net_count', 0)}</p>
        <p><strong>Risk Count:</strong> {board_summary.get('risk_count', 0)}</p>
        <p><strong>Sample Components:</strong> {escape(', '.join(board_summary.get('sample_components', [])))}</p>
    """

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
        <title>Silicore Engineering Report</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 32px;
                background: #f8fafc;
                color: #0f172a;
            }}
            .card {{
                background: white;
                border: 1px solid #cbd5e1;
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 20px;
            }}
            .risk {{
                margin-top: 12px;
                padding-top: 12px;
                border-top: 1px solid #e2e8f0;
            }}
        </style>
    </head>
    <body>
        <h1>Silicore Engineering Report</h1>

        <div class="card">
            <p><strong>File:</strong> {escape(result['filename'])}</p>
            <p><strong>Score:</strong> {result['score']} / 10</p>
            <p><strong>Total Risks:</strong> {len(result['risks'])}</p>
            <p><strong>Total Penalty:</strong> {result['score_explanation'].get('total_penalty', 0)}</p>

            <h3>Board Summary</h3>
            {board_summary_html}

            <h3>Severity Penalties</h3>
            <ul>{severity_items}</ul>

            <h3>Category Penalties</h3>
            <ul>{category_items}</ul>
        </div>

        <div class="card">
            <h2>Detailed Findings</h2>
            {risks_html}
        </div>
    </body>
    </html>
    """

    with open(path, "w", encoding="utf-8") as file:
        file.write(html)


def _build_project_summary(boards):
    if not boards:
        return {
            "total_boards": 0,
            "average_score": 0,
            "best_score": 0,
            "worst_score": 0,
            "severity_counts": {},
            "category_counts": {}
        }

    total_score = sum(board.get("score", 0) for board in boards)
    average_score = round(total_score / len(boards), 2)
    best_score = max(board.get("score", 0) for board in boards)
    worst_score = min(board.get("score", 0) for board in boards)

    severity_counts = {}
    category_counts = {}

    for board in boards:
        for risk in board.get("risks", []):
            severity = risk.get("severity", "unknown")
            category = risk.get("category", "unknown")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            category_counts[category] = category_counts.get(category, 0) + 1

    return {
        "total_boards": len(boards),
        "average_score": average_score,
        "best_score": best_score,
        "worst_score": worst_score,
        "severity_counts": severity_counts,
        "category_counts": category_counts
    }


def _write_project_markdown(path, project_data):
    summary = project_data["summary"]
    boards = project_data["boards"]

    lines = [
        "# SILICORE PROJECT SUMMARY",
        "",
        f"- Total Boards: {summary['total_boards']}",
        f"- Average Score: {summary['average_score']} / 10",
        f"- Best Score: {summary['best_score']} / 10",
        f"- Worst Score: {summary['worst_score']} / 10",
        "",
        "## Board Rankings",
        ""
    ]

    for index, board in enumerate(boards, start=1):
        lines.append(f"### #{index} {board['filename']}")
        lines.append(f"- Score: {board['score']} / 10")
        lines.append(f"- Total Risks: {len(board.get('risks', []))}")
        lines.append(f"- Total Penalty: {board.get('score_explanation', {}).get('total_penalty', 0)}")

        board_summary = board.get("board_summary", {})
        lines.append(f"- Component Count: {board_summary.get('component_count', 0)}")
        lines.append(f"- Net Count: {board_summary.get('net_count', 0)}")
        lines.append("")

    with open(path, "w", encoding="utf-8") as file:
        file.write("\n".join(lines))


def _write_project_html(path, project_data):
    summary = project_data["summary"]
    boards = project_data["boards"]

    boards_html = ""
    for index, board in enumerate(boards, start=1):
        board_summary = board.get("board_summary", {})
        boards_html += f"""
        <div class="board">
            <h2>#{index} {escape(str(board['filename']))}</h2>
            <p><strong>Score:</strong> {board['score']} / 10</p>
            <p><strong>Total Risks:</strong> {len(board.get('risks', []))}</p>
            <p><strong>Total Penalty:</strong> {board.get('score_explanation', {}).get('total_penalty', 0)}</p>
            <p><strong>Component Count:</strong> {board_summary.get('component_count', 0)}</p>
            <p><strong>Net Count:</strong> {board_summary.get('net_count', 0)}</p>
        </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Silicore Project Summary</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 32px;
                background: #f8fafc;
                color: #0f172a;
            }}
            .card {{
                background: white;
                border: 1px solid #cbd5e1;
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 20px;
            }}
            .board {{
                background: white;
                border: 1px solid #cbd5e1;
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 20px;
            }}
        </style>
    </head>
    <body>
        <h1>Silicore Project Summary</h1>

        <div class="card">
            <p><strong>Total Boards:</strong> {summary['total_boards']}</p>
            <p><strong>Average Score:</strong> {summary['average_score']} / 10</p>
            <p><strong>Best Score:</strong> {summary['best_score']} / 10</p>
            <p><strong>Worst Score:</strong> {summary['worst_score']} / 10</p>
        </div>

        {boards_html}
    </body>
    </html>
    """

    with open(path, "w", encoding="utf-8") as file:
        file.write(html)


def run_single_analysis_from_path(file_path, config=None, output_dir=None):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Board file not found: {file_path}")

    if config is None:
        config = load_config("custom_config.json")

    pcb = _load_board(file_path)
    pcb = _normalize_board(pcb)

    risks, _raw_engine_result = _run_rule_engine(pcb, config)

    score, score_explanation = _compute_score_and_explanation(risks, config)
    board_summary = _build_board_summary(pcb, risks, os.path.basename(file_path))

    result = {
        "filename": os.path.basename(file_path),
        "score": score,
        "risks": risks,
        "score_explanation": score_explanation,
        "board_summary": board_summary
    }

    if output_dir is not None:
        os.makedirs(output_dir, exist_ok=True)

        json_path = os.path.join(output_dir, "single_analysis.json")
        md_path = os.path.join(output_dir, "single_report.md")
        html_path = os.path.join(output_dir, "single_report.html")

        _write_json(json_path, result)
        _write_single_markdown(md_path, result)
        _write_single_html(html_path, result)

        result["json_path"] = json_path
        result["report_md_path"] = md_path
        result["report_html_path"] = html_path
    else:
        result["json_path"] = None
        result["report_md_path"] = None
        result["report_html_path"] = None

    print(f"[Silicore Debug] {board_summary}")

    return result


def analyze_project_paths(file_paths, config=None, output_dir=None):
    if config is None:
        config = load_config("custom_config.json")

    boards = []

    for file_path in file_paths:
        boards.append(run_single_analysis_from_path(file_path, config=config))

    boards = sorted(boards, key=lambda board: board.get("score", 0), reverse=True)

    for index, board in enumerate(boards, start=1):
        board["rank"] = index

    summary = _build_project_summary(boards)

    project_data = {
        "generated_at": datetime.now().isoformat(),
        "summary": summary,
        "boards": boards
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

    return {
        "boards": boards,
        "summary": summary,
        "summary_json_path": summary_json_path,
        "summary_md_path": summary_md_path,
        "summary_html_path": summary_html_path
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
            "summary_json_path": None,
            "summary_md_path": None,
            "summary_html_path": None
        }

    output_dir = os.path.join(directory_path, "silicore_outputs")
    os.makedirs(output_dir, exist_ok=True)

    return analyze_project_paths(file_paths, config=config, output_dir=output_dir)


def analyze_single_board(uploaded_file, upload_folder, runs_folder, config_path):
    if not uploaded_file or uploaded_file.filename == "":
        raise ValueError("Please upload a board file.")

    ensure_runs_folder(runs_folder)
    ensure_clean_upload_dir(upload_folder)

    config = load_config(config_path)

    filename = safe_filename(uploaded_file.filename)
    file_path = os.path.join(upload_folder, filename)
    uploaded_file.save(file_path)

    run_dir_name, result_output_dir = create_run_directory("single", runs_folder)

    analysis_result = run_single_analysis_from_path(
        file_path,
        config=config,
        output_dir=result_output_dir
    )

    save_run_meta(result_output_dir, {
        "run_type": "single",
        "created_at": datetime.now().isoformat(),
        "filename": filename
    })

    return {
        "config_view": get_editable_config_view(config),
        "result": {
            "filename": filename,
            "score": analysis_result.get("score", 0),
            "risks": analysis_result.get("risks", []),
            "score_explanation": analysis_result.get("score_explanation", {}),
            "board_summary": analysis_result.get("board_summary", {}),
            "downloads": build_single_downloads(run_dir_name)
        }
    }


def analyze_project_files(uploaded_files, upload_folder, runs_folder, config_path):
    valid_files = [
        file for file in uploaded_files
        if file and file.filename and file.filename.strip()
    ]

    if not valid_files:
        raise ValueError("Please upload at least one project file.")

    ensure_runs_folder(runs_folder)
    ensure_clean_upload_dir(upload_folder)

    config = load_config(config_path)

    saved_paths = []
    saved_names = []

    for uploaded_file in valid_files:
        filename = safe_filename(uploaded_file.filename)
        file_path = os.path.join(upload_folder, filename)
        uploaded_file.save(file_path)
        saved_paths.append(file_path)
        saved_names.append(filename)

    run_dir_name, result_output_dir = create_run_directory("project", runs_folder)

    project_analysis = analyze_project_paths(
        saved_paths,
        config=config,
        output_dir=result_output_dir
    )

    save_run_meta(result_output_dir, {
        "run_type": "project",
        "created_at": datetime.now().isoformat(),
        "filenames": saved_names,
        "board_count": len(saved_names)
    })

    return {
        "config_view": get_editable_config_view(config),
        "project_result": {
            "boards": project_analysis.get("boards", []),
            "downloads": build_project_downloads(run_dir_name)
        }
    }