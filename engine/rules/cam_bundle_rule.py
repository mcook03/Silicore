from collections import Counter

from engine.geometry_backend import polygon_area
from engine.risk import make_risk


def _outline_is_closed(outline_segments, tolerance=0.25):
    if not outline_segments:
        return False
    points = []
    for segment in outline_segments:
        points.append((round(segment.x1, 3), round(segment.y1, 3)))
        points.append((round(segment.x2, 3), round(segment.y2, 3)))
    counts = Counter(points)
    odd_points = [point for point, count in counts.items() if count % 2 != 0]
    return len(odd_points) == 0


def run_rule(pcb, config):
    risks = []
    rule_config = config.get("rules", {}).get("cam_bundle", {})
    if not str(getattr(pcb, "source_format", "")).startswith("gerber"):
        return risks

    require_outline = bool(rule_config.get("require_outline", True))
    require_drill = bool(rule_config.get("require_drill", True))
    min_copper_area_ratio = float(rule_config.get("min_copper_area_ratio", 0.005))

    cam_meta = getattr(pcb, "metadata", {}).get("cam", {})
    layer_files = cam_meta.get("layer_files") or cam_meta.get("merged_sources") or []
    copper_layers = [layer for layer in getattr(pcb, "declared_layers", []) if "copper" in str(layer).lower()]
    board_area = max(float(getattr(pcb, "board_width", 0.0) or 0.0) * float(getattr(pcb, "board_height", 0.0) or 0.0), 0.0)
    copper_area = sum(polygon_area(getattr(zone, "points", [])) for zone in getattr(pcb, "zones", []))
    copper_area_ratio = (copper_area / board_area) if board_area > 0 else 0.0

    if require_outline and not getattr(pcb, "outline_segments", []):
        risks.append(
            make_risk(
                rule_id="cam_bundle",
                category="manufacturing",
                severity="high",
                message="Gerber/CAM bundle does not include a recognizable board outline.",
                recommendation="Include a profile or edge-cuts layer in the CAM export so fabrication shape and board bounds are unambiguous.",
                metrics={"outline_count": 0},
                confidence=0.94,
                short_title="Missing CAM outline",
                fix_priority="high",
                estimated_impact="high",
                design_domain="manufacturing",
                why_it_matters="A missing board outline makes CAM import incomplete and weakens manufacturability and keepout reasoning.",
                trigger_condition="CAM review expected a board outline layer but did not find one.",
                threshold_label="Outline layer required",
                observed_label="Observed outline segments 0",
            )
        )
    elif getattr(pcb, "outline_segments", []) and not _outline_is_closed(getattr(pcb, "outline_segments", [])):
        risks.append(
            make_risk(
                rule_id="cam_bundle_outline",
                category="manufacturing",
                severity="high",
                message="Gerber/CAM outline appears open or fragmented instead of closed.",
                recommendation="Repair the profile/outline layer so the board perimeter is fully closed before fabrication review.",
                metrics={"outline_count": len(getattr(pcb, "outline_segments", []))},
                confidence=0.86,
                short_title="Open CAM outline",
                fix_priority="high",
                estimated_impact="high",
                design_domain="manufacturing",
                why_it_matters="An open board outline can produce fabrication ambiguity and weakens all board-area-based geometry analysis.",
                trigger_condition="Outline segment graph did not resolve into a closed perimeter.",
                threshold_label="Closed outline perimeter required",
                observed_label="Observed open perimeter geometry",
            )
        )

    if require_drill and copper_layers and not getattr(pcb, "vias", []):
        risks.append(
            make_risk(
                rule_id="cam_bundle_drill",
                category="manufacturing",
                severity="medium",
                message="Gerber/CAM bundle has copper layers but no drill hits were recognized.",
                recommendation="Include Excellon drill output in the CAM package so through-hole and via features can be reviewed accurately.",
                metrics={"drill_hits": len(getattr(pcb, "vias", []))},
                confidence=0.82,
                short_title="No drill file recognized",
                fix_priority="medium",
                estimated_impact="moderate",
                design_domain="manufacturing",
                why_it_matters="Without drill data, via, tooling, and hole-related manufacturability checks are incomplete.",
                trigger_condition="CAM bundle contained copper content without recognized drill geometry.",
                threshold_label="Drill geometry expected for copper bundle",
                observed_label="Observed drill hits 0",
            )
        )

    if board_area > 0 and copper_layers and copper_area_ratio < min_copper_area_ratio:
        risks.append(
            make_risk(
                rule_id="cam_bundle_copper",
                category="manufacturing",
                severity="medium",
                message=f"Recognized copper-region coverage is very low for this CAM job ({copper_area_ratio:.4f} of board area).",
                recommendation="Verify that copper pours, flashes, and region features were exported correctly and that the CAM bundle is complete.",
                metrics={"copper_area_ratio": round(copper_area_ratio, 6), "threshold": min_copper_area_ratio},
                confidence=0.74,
                short_title="Low CAM copper coverage",
                fix_priority="medium",
                estimated_impact="moderate",
                design_domain="manufacturing",
                why_it_matters="Very low recognized copper coverage can indicate incomplete CAM export or a parser/import mismatch.",
                trigger_condition="Recognized copper-region area fell below the configured minimum CAM coverage ratio.",
                threshold_label=f"Minimum copper area ratio {min_copper_area_ratio:.4f}",
                observed_label=f"Observed copper area ratio {copper_area_ratio:.4f}",
            )
        )

    if layer_files and len(layer_files) < int(rule_config.get("min_layer_files", 2)):
        risks.append(
            make_risk(
                rule_id="cam_bundle_layers",
                category="manufacturing",
                severity="medium",
                message="CAM bundle contains very few recognized layer files for a full fabrication review.",
                recommendation="Export the full CAM set, including copper, outline/profile, drill, and any critical mask/silkscreen layers used for review.",
                metrics={"layer_file_count": len(layer_files)},
                confidence=0.79,
                short_title="Sparse CAM bundle",
                fix_priority="medium",
                estimated_impact="moderate",
                design_domain="manufacturing",
                why_it_matters="Sparse CAM bundles weaken confidence that geometry-backed review covers the real fabrication package.",
                trigger_condition="Recognized CAM layer-file count fell below the minimum configured review bundle threshold.",
                threshold_label=f"Minimum CAM files {int(rule_config.get('min_layer_files', 2))}",
                observed_label=f"Observed CAM files {len(layer_files)}",
            )
        )

    return risks
