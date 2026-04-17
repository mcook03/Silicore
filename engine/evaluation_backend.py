import os
from collections import defaultdict

from engine.db import list_evaluation_runs, record_evaluation_run
from engine.job_store import update_job
from engine.services.analysis_service import run_single_analysis_from_path


SUPPORTED_FIXTURE_EXTENSIONS = [
    ".kicad_pcb",
    ".brd",
    ".txt",
    ".gbr",
    ".gko",
    ".ger",
    ".gtl",
    ".gbl",
    ".gto",
    ".gbo",
    ".gts",
    ".gbs",
    ".gm1",
    ".pho",
    ".art",
    ".outline",
    ".drl",
    ".xln",
    ".zip",
    ".pcbdocascii",
]


def _is_supported_fixture_file(name):
    return any(name.lower().endswith(ext) for ext in SUPPORTED_FIXTURE_EXTENSIONS)


def _looks_like_cam_directory(path):
    try:
        names = os.listdir(path)
    except OSError:
        return False
    return any(_is_supported_fixture_file(name) for name in names)


def _evaluate_directory(source_dir="fixtures", config="custom_config.json", scope="fixtures", label=None):
    if not os.path.isdir(source_dir):
        return {
            "scope": scope,
            "label": label or scope.replace("_", " ").title(),
            "fixture_count": 0,
            "average_score": 0.0,
            "categories": [],
            "formats": [],
            "boards": [],
        }

    supported = []
    for name in sorted(os.listdir(source_dir)):
        path = os.path.join(source_dir, name)
        if os.path.isdir(path) and _looks_like_cam_directory(path):
            supported.append(path)
            continue
        if os.path.isfile(path) and _is_supported_fixture_file(name):
            supported.append(path)

    boards = []
    category_counts = defaultdict(int)
    format_counts = defaultdict(int)
    parser_confidence_by_format = defaultdict(list)
    source_family_counts = defaultdict(int)
    source_family_ready = defaultdict(int)
    total_score = 0.0
    parser_confidence_total = 0.0
    parser_confidence_count = 0
    failed_boards = 0
    cam_bundle_count = 0
    cam_ready_count = 0
    cam_missing_signal_counts = defaultdict(int)
    cam_readiness_bands = defaultdict(int)

    for path in supported:
        try:
            result = run_single_analysis_from_path(path, config=config)
            parser_confidence = float(((result.get("parser_confidence") or {}).get("score")) or 0)
            cam_summary = result.get("cam_summary") or {}
            if cam_summary.get("active"):
                cam_bundle_count += 1
                if cam_summary.get("complete"):
                    cam_ready_count += 1
                source_family = str(cam_summary.get("source_family") or "generic_gerber")
                source_family_counts[source_family] += 1
                if cam_summary.get("complete"):
                    source_family_ready[source_family] += 1
                for signal in cam_summary.get("missing_signals") or []:
                    cam_missing_signal_counts[str(signal)] += 1
                cam_readiness_bands[str(cam_summary.get("readiness_level") or "unknown")] += 1
            format_key = (result.get("cam_summary") or {}).get("source_format") or os.path.splitext(path)[1].lower() or "directory"
            boards.append(
                {
                    "filename": result.get("filename"),
                    "score": result.get("score", 0),
                    "risk_count": len(result.get("risks", []) or []),
                    "format": format_key,
                    "dominant_subsystem": ((result.get("subsystem_summary") or {}).get("dominant_subsystem") or "General"),
                    "parser_confidence": parser_confidence,
                    "stackup_style": ((result.get("stackup_summary") or {}).get("style") or "unknown"),
                    "cam_ready": bool(cam_summary.get("complete")),
                    "cam_readiness_score": cam_summary.get("readiness_score", 0),
                    "cam_bundle_type": cam_summary.get("bundle_type"),
                    "cam_missing_signals": cam_summary.get("missing_signals") or [],
                    "cam_remediation_steps": cam_summary.get("remediation_steps") or [],
                    "cam_readiness_level": cam_summary.get("readiness_level") or "unknown",
                }
            )
            total_score += float(result.get("score", 0) or 0)
            parser_confidence_total += parser_confidence
            parser_confidence_count += 1
            format_counts[format_key] += 1
            parser_confidence_by_format[format_key].append(parser_confidence)
            for risk in result.get("risks", []) or []:
                category_counts[str(risk.get("category") or "unknown")] += 1
        except Exception as exc:
            failed_boards += 1
            boards.append(
                {
                    "filename": os.path.basename(path.rstrip(os.sep)),
                    "score": 0,
                    "risk_count": 0,
                    "format": os.path.splitext(path)[1].lower() or "directory",
                    "dominant_subsystem": "Unknown",
                    "parser_confidence": 0,
                    "stackup_style": "unknown",
                    "error": str(exc),
                }
            )

    fixture_count = len(boards)
    summary = {
        "scope": scope,
        "label": label or scope.replace("_", " ").title(),
        "fixture_count": fixture_count,
        "average_score": round(total_score / fixture_count, 1) if fixture_count else 0.0,
        "average_parser_confidence": round(parser_confidence_total / parser_confidence_count, 1) if parser_confidence_count else 0.0,
        "failed_board_count": failed_boards,
        "categories": [
            {"label": key.replace("_", " ").title(), "count": value}
            for key, value in sorted(category_counts.items(), key=lambda item: (-item[1], item[0]))
        ],
        "formats": [
            {
                "label": key,
                "count": value,
                "average_parser_confidence": round(sum(parser_confidence_by_format.get(key, [])) / len(parser_confidence_by_format.get(key, [1])), 1)
                if parser_confidence_by_format.get(key)
                else 0.0,
            }
            for key, value in sorted(format_counts.items(), key=lambda item: item[0])
        ],
        "boards": boards,
        "parser_health": {
            "average_confidence": round(parser_confidence_total / parser_confidence_count, 1) if parser_confidence_count else 0.0,
            "supported_formats": len(format_counts),
            "failed_boards": failed_boards,
            "weakest_boards": sorted(
                [
                    {
                        "filename": board.get("filename"),
                        "format": board.get("format"),
                        "parser_confidence": board.get("parser_confidence", 0),
                    }
                    for board in boards
                    if board.get("filename")
                ],
                key=lambda item: (item.get("parser_confidence", 0), str(item.get("filename") or "").lower()),
            )[:5],
        },
        "cam_health": {
            "bundle_count": cam_bundle_count,
            "review_ready_bundles": cam_ready_count,
            "readiness_ratio": round((cam_ready_count / cam_bundle_count) * 100, 1) if cam_bundle_count else 0.0,
            "missing_signals": [
                {"label": key, "count": value}
                for key, value in sorted(cam_missing_signal_counts.items(), key=lambda item: (-item[1], item[0]))
            ],
            "readiness_bands": [
                {"label": key.replace("_", " ").title(), "count": value}
                for key, value in sorted(cam_readiness_bands.items(), key=lambda item: item[0])
            ],
            "source_families": [
                {
                    "label": key.replace("_", " ").title(),
                    "count": value,
                    "ready_count": source_family_ready.get(key, 0),
                    "readiness_ratio": round((source_family_ready.get(key, 0) / value) * 100, 1) if value else 0.0,
                }
                for key, value in sorted(source_family_counts.items(), key=lambda item: item[0])
            ],
        },
    }
    try:
        record = record_evaluation_run(summary, scope=scope)
        summary["evaluation_id"] = record.get("evaluation_id")
    except Exception:
        summary["evaluation_id"] = None
    return summary


def evaluate_fixture_suite(fixtures_dir="fixtures", config="custom_config.json"):
    return _evaluate_directory(
        source_dir=fixtures_dir,
        config=config,
        scope="fixtures",
        label="Fixture Benchmark",
    )


def evaluate_external_suite(samples_dir, config="custom_config.json", label=None):
    return _evaluate_directory(
        source_dir=samples_dir,
        config=config,
        scope="external",
        label=label or "External Validation",
    )


def summarize_evaluation_history(limit=20):
    runs = list_evaluation_runs(limit=limit)
    fixture_runs = [item for item in runs if item.get("scope") == "fixtures"]
    external_runs = [item for item in runs if item.get("scope") == "external"]

    def _trend(items, key):
        if len(items) < 2:
            return 0.0
        return round(float(items[0].get(key) or 0.0) - float(items[1].get(key) or 0.0), 1)

    latest_fixture = fixture_runs[0].get("summary") if fixture_runs else {}
    latest_external = external_runs[0].get("summary") if external_runs else {}
    return {
        "history_count": len(runs),
        "fixture_runs": len(fixture_runs),
        "external_runs": len(external_runs),
        "fixture_score_trend": _trend(fixture_runs, "average_score"),
        "fixture_parser_confidence_trend": _trend(fixture_runs, "average_parser_confidence"),
        "external_parser_confidence_trend": _trend(external_runs, "average_parser_confidence"),
        "external_failure_trend": _trend(external_runs, "failed_board_count"),
        "fixture_cam_readiness_ratio": ((latest_fixture.get("cam_health") or {}).get("readiness_ratio", 0.0) if latest_fixture else 0.0),
        "external_cam_readiness_ratio": ((latest_external.get("cam_health") or {}).get("readiness_ratio", 0.0) if latest_external else 0.0),
        "latest_fixture_weakest_cases": ((latest_fixture.get("parser_health") or {}).get("weakest_boards") or [])[:5] if latest_fixture else [],
        "latest_external_weakest_cases": ((latest_external.get("parser_health") or {}).get("weakest_boards") or [])[:5] if latest_external else [],
    }


def run_evaluation_job(job_id, fixtures_dir="fixtures", config="custom_config.json"):
    update_job(job_id, status="running")
    try:
        result = _evaluate_directory(source_dir=fixtures_dir, config=config, scope="fixtures", label="Fixture Benchmark")
        update_job(job_id, status="completed", result=result)
        return result
    except Exception as exc:
        update_job(job_id, status="failed", error_text=str(exc))
        raise


def run_external_evaluation_job(job_id, samples_dir, config="custom_config.json", label=None):
    update_job(job_id, status="running")
    try:
        if not samples_dir or not os.path.isdir(samples_dir):
            raise ValueError("External evaluation samples directory is missing or unreadable.")
        result = evaluate_external_suite(samples_dir, config=config, label=label)
        update_job(job_id, status="completed", result=result)
        return result
    except Exception as exc:
        update_job(job_id, status="failed", error_text=str(exc))
        raise
