import os
from collections import defaultdict

from engine.job_store import update_job
from engine.services.analysis_service import run_single_analysis_from_path


def evaluate_fixture_suite(fixtures_dir="fixtures", config="custom_config.json"):
    if not os.path.isdir(fixtures_dir):
        return {
            "fixture_count": 0,
            "average_score": 0.0,
            "categories": [],
            "formats": [],
            "boards": [],
        }

    supported = []
    for name in sorted(os.listdir(fixtures_dir)):
        path = os.path.join(fixtures_dir, name)
        if not os.path.isfile(path):
            continue
        if not any(name.lower().endswith(ext) for ext in [".kicad_pcb", ".brd", ".txt", ".gbr", ".gko", ".ger", ".pcbdocascii"]):
            continue
        supported.append(path)

    boards = []
    category_counts = defaultdict(int)
    format_counts = defaultdict(int)
    total_score = 0.0
    parser_confidence_total = 0.0
    parser_confidence_count = 0
    failed_boards = 0

    for path in supported:
        try:
            result = run_single_analysis_from_path(path, config=config)
            parser_confidence = float(((result.get("parser_confidence") or {}).get("score")) or 0)
            boards.append(
                {
                    "filename": result.get("filename"),
                    "score": result.get("score", 0),
                    "risk_count": len(result.get("risks", []) or []),
                    "format": os.path.splitext(path)[1].lower(),
                    "dominant_subsystem": ((result.get("subsystem_summary") or {}).get("dominant_subsystem") or "General"),
                    "parser_confidence": parser_confidence,
                    "stackup_style": ((result.get("stackup_summary") or {}).get("style") or "unknown"),
                }
            )
            total_score += float(result.get("score", 0) or 0)
            parser_confidence_total += parser_confidence
            parser_confidence_count += 1
            format_counts[os.path.splitext(path)[1].lower()] += 1
            for risk in result.get("risks", []) or []:
                category_counts[str(risk.get("category") or "unknown")] += 1
        except Exception as exc:
            failed_boards += 1
            boards.append(
                {
                    "filename": os.path.basename(path),
                    "score": 0,
                    "risk_count": 0,
                    "format": os.path.splitext(path)[1].lower(),
                    "dominant_subsystem": "Unknown",
                    "parser_confidence": 0,
                    "stackup_style": "unknown",
                    "error": str(exc),
                }
            )

    fixture_count = len(boards)
    return {
        "fixture_count": fixture_count,
        "average_score": round(total_score / fixture_count, 1) if fixture_count else 0.0,
        "average_parser_confidence": round(parser_confidence_total / parser_confidence_count, 1) if parser_confidence_count else 0.0,
        "failed_board_count": failed_boards,
        "categories": [
            {"label": key.replace("_", " ").title(), "count": value}
            for key, value in sorted(category_counts.items(), key=lambda item: (-item[1], item[0]))
        ],
        "formats": [
            {"label": key, "count": value}
            for key, value in sorted(format_counts.items(), key=lambda item: item[0])
        ],
        "boards": boards,
        "parser_health": {
            "average_confidence": round(parser_confidence_total / parser_confidence_count, 1) if parser_confidence_count else 0.0,
            "supported_formats": len(format_counts),
            "failed_boards": failed_boards,
        },
    }


def run_evaluation_job(job_id, fixtures_dir="fixtures", config="custom_config.json"):
    update_job(job_id, status="running")
    try:
        result = evaluate_fixture_suite(fixtures_dir=fixtures_dir, config=config)
        update_job(job_id, status="completed", result=result)
        return result
    except Exception as exc:
        update_job(job_id, status="failed", error_text=str(exc))
        raise
