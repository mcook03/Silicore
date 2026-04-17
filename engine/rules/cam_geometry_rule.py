from engine.geometry_backend import (
    flash_to_polygon,
    line_to_polygon,
    polygon_distance,
)
from engine.risk import make_risk


def _layer_set(value):
    if not value:
        return set()
    if isinstance(value, str):
        return {item.strip() for item in value.split(",") if item.strip()}
    return {str(item).strip() for item in value if str(item).strip()}


def _build_regions(pcb):
    regions = []

    for component in getattr(pcb, "components", []):
        for pad in getattr(component, "pads", []):
            diameter = max(float(getattr(pad, "size_x", 0.0) or 0.0), float(getattr(pad, "size_y", 0.0) or 0.0), 0.18)
            polygon = flash_to_polygon(pad.x, pad.y, diameter, shape="rect" if abs((pad.size_x or 0) - (pad.size_y or 0)) > 0.02 else "circle", size_x=pad.size_x, size_y=pad.size_y)
            regions.append(
                {
                    "kind": "pad",
                    "component_ref": component.ref,
                    "pad_name": pad.pad_name,
                    "net_name": str(getattr(pad, "net_name", "") or "").upper(),
                    "layers": _layer_set(getattr(pad, "layer", "")) or _layer_set(component.layer),
                    "polygon": polygon,
                    "region": {"x": pad.x, "y": pad.y},
                }
            )

    for via in getattr(pcb, "vias", []):
        diameter = max(float(getattr(via, "diameter", 0.0) or 0.0), 0.18)
        polygon = flash_to_polygon(via.x, via.y, diameter)
        regions.append(
            {
                "kind": "via",
                "component_ref": "",
                "pad_name": "",
                "net_name": str(getattr(via, "net_name", "") or "").upper(),
                "layers": _layer_set(getattr(via, "layers", [])),
                "polygon": polygon,
                "region": {"x": via.x, "y": via.y},
            }
        )

    for trace in getattr(pcb, "traces", []):
        polygon = line_to_polygon([(trace.x1, trace.y1), (trace.x2, trace.y2)], width=float(getattr(trace, "width", 0.2) or 0.2))
        regions.append(
            {
                "kind": "trace",
                "component_ref": "",
                "pad_name": "",
                "net_name": str(getattr(trace, "net_name", "") or "").upper(),
                "layers": _layer_set(getattr(trace, "layer", "")),
                "polygon": polygon,
                "region": {"x": (trace.x1 + trace.x2) / 2.0, "y": (trace.y1 + trace.y2) / 2.0},
            }
        )

    for zone in getattr(pcb, "zones", []):
        if len(getattr(zone, "points", [])) < 3:
            continue
        regions.append(
            {
                "kind": "zone",
                "component_ref": "",
                "pad_name": "",
                "net_name": str(getattr(zone, "net_name", "") or "").upper(),
                "layers": _layer_set(getattr(zone, "layer", "")),
                "polygon": list(zone.points),
                "region": zone.points[0] if zone.points else None,
            }
        )

    return regions


def _shares_layer(left, right):
    left_layers = left.get("layers") or set()
    right_layers = right.get("layers") or set()
    if not left_layers or not right_layers:
        return True
    return bool(left_layers & right_layers)


def _matches_any(net_name, keywords):
    upper = str(net_name or "").upper()
    return any(keyword in upper for keyword in keywords)


def run_rule(pcb, config):
    risks = []
    rule_config = config.get("rules", {}).get("cam_geometry", {})
    if not getattr(pcb, "traces", None) and not getattr(pcb, "zones", None):
        return risks

    min_clearance = float(rule_config.get("min_clearance", 0.18))
    min_creepage = float(rule_config.get("min_creepage", 2.5))
    hv_keywords = [str(item).upper() for item in rule_config.get("high_voltage_net_keywords", ["HV", "VBUS", "PACK", "BATT", "VAC", "VDC"])]
    regions = _build_regions(pcb)

    for index, left in enumerate(regions):
        for right in regions[index + 1 :]:
            if not _shares_layer(left, right):
                continue
            left_net = left.get("net_name") or ""
            right_net = right.get("net_name") or ""
            if left_net and right_net and left_net == right_net:
                continue

            distance = polygon_distance(left.get("polygon"), right.get("polygon"))
            if distance is None:
                continue

            if distance < min_clearance:
                components = [item for item in [left.get("component_ref"), right.get("component_ref")] if item]
                nets = [item for item in [left_net, right_net] if item]
                risks.append(
                    make_risk(
                        rule_id="cam_geometry",
                        category="manufacturing",
                        severity="high",
                        message=f"Geometry-derived copper clearance between {left.get('kind')} and {right.get('kind')} falls below target ({distance:.3f})",
                        recommendation="Increase copper-to-copper spacing or reshape the nearby region to restore manufacturable and electrically safe clearance.",
                        components=components,
                        nets=nets,
                        region=left.get("region") or right.get("region"),
                        metrics={"clearance": round(distance, 4), "threshold": min_clearance},
                        confidence=0.92,
                        short_title="Geometry clearance below target",
                        fix_priority="high",
                        estimated_impact="high",
                        design_domain="manufacturing",
                        why_it_matters="True copper-region spacing is more reliable than center-point spacing for manufacturability and safety review.",
                        trigger_condition="Buffered copper geometry distance fell below the configured CAM clearance threshold.",
                        threshold_label=f"Minimum CAM clearance {min_clearance:.3f}",
                        observed_label=f"Observed copper clearance {distance:.3f}",
                    )
                )

            if _matches_any(left_net, hv_keywords) or _matches_any(right_net, hv_keywords):
                if distance < min_creepage:
                    components = [item for item in [left.get("component_ref"), right.get("component_ref")] if item]
                    nets = [item for item in [left_net, right_net] if item]
                    risks.append(
                        make_risk(
                            rule_id="cam_geometry_creepage",
                            category="safety_high_voltage",
                            severity="critical",
                            message=f"Geometry-derived high-voltage spacing between {left.get('kind')} and {right.get('kind')} is below creepage target ({distance:.3f})",
                            recommendation="Increase the routed spacing, add slots/barriers, or rework the high-voltage region to meet creepage intent.",
                            components=components,
                            nets=nets,
                            region=left.get("region") or right.get("region"),
                            metrics={"creepage": round(distance, 4), "threshold": min_creepage},
                            confidence=0.9,
                            short_title="Geometry creepage below target",
                            fix_priority="high",
                            estimated_impact="high",
                            design_domain="safety",
                            why_it_matters="Geometry-derived region spacing is a stronger basis for high-voltage creepage review than simple pad-center distance.",
                            trigger_condition="High-voltage copper-region spacing fell below the configured geometry creepage threshold.",
                            threshold_label=f"Minimum geometry creepage {min_creepage:.3f}",
                            observed_label=f"Observed geometry creepage {distance:.3f}",
                        )
                    )

    return risks
