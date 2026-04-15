from math import sqrt

from engine.risk import make_risk


def _distance(x1, y1, x2, y2):
    return sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


def run_rule(pcb, config):
    risks = []
    rule_config = config.get("rules", {}).get("manufacturability", {})
    signal_config = config.get("signal", {})

    min_trace_width = float(
        rule_config.get(
            "min_trace_width",
            signal_config.get("min_general_trace_width", 0.15),
        )
    )
    min_drill = float(rule_config.get("min_drill", 0.2))
    min_annular_ring = float(rule_config.get("min_annular_ring", 0.1))
    via_in_pad_distance = float(rule_config.get("via_in_pad_distance", 0.35))

    for net_name, net in getattr(pcb, "nets", {}).items():
        for segment in getattr(net, "trace_segments", []):
            if getattr(segment, "width", 0.0) < min_trace_width:
                risks.append(
                    make_risk(
                        rule_id="manufacturability",
                        category="manufacturing",
                        severity="medium",
                        message=f"Net {net_name} uses a trace width below the fab-oriented limit ({segment.width:.2f})",
                        recommendation="Increase the trace width or confirm that the chosen board house can reliably build this geometry.",
                        nets=[net_name],
                        metrics={
                            "trace_width": round(segment.width, 3),
                            "threshold": min_trace_width,
                        },
                        confidence=0.9,
                        short_title="Trace width below fab target",
                        fix_priority="medium",
                        estimated_impact="moderate",
                        design_domain="manufacturing",
                        why_it_matters="Very narrow traces can reduce yield margin, increase fabrication cost, or violate shop minimums.",
                        trigger_condition="Trace width fell below the configured manufacturability threshold.",
                        threshold_label=f"Minimum manufacturable width {min_trace_width:.2f}",
                        observed_label=f"Observed trace width {segment.width:.2f}",
                    )
                )

    for via in getattr(pcb, "vias", []):
        annular_ring = max((float(via.diameter) - float(via.drill)) / 2, 0.0)

        if float(via.drill) < min_drill:
            risks.append(
                make_risk(
                    rule_id="manufacturability",
                    category="manufacturing",
                    severity="medium",
                    message=f"Via on net {via.net_name} uses a very small drill size ({via.drill:.2f})",
                    recommendation="Increase the drill size or confirm advanced fab capability for this via structure.",
                    nets=[via.net_name],
                    metrics={
                        "drill": round(float(via.drill), 3),
                        "threshold": min_drill,
                    },
                    confidence=0.88,
                    short_title="Small via drill",
                    fix_priority="medium",
                    estimated_impact="moderate",
                    design_domain="manufacturing",
                    why_it_matters="Very small drills can push fabrication cost up and reduce process margin.",
                    trigger_condition="Via drill size fell below the configured minimum manufacturable drill threshold.",
                    threshold_label=f"Minimum drill {min_drill:.2f}",
                    observed_label=f"Observed drill {via.drill:.2f}",
                )
            )

        if annular_ring < min_annular_ring:
            risks.append(
                make_risk(
                    rule_id="manufacturability",
                    category="manufacturing",
                    severity="high",
                    message=f"Via on net {via.net_name} has a small annular ring ({annular_ring:.2f})",
                    recommendation="Increase via diameter or reduce drill size to improve annular-ring robustness.",
                    nets=[via.net_name],
                    metrics={
                        "annular_ring": round(annular_ring, 3),
                        "threshold": min_annular_ring,
                    },
                    confidence=0.9,
                    short_title="Annular ring too small",
                    fix_priority="high",
                    estimated_impact="high",
                    design_domain="manufacturing",
                    why_it_matters="Insufficient annular ring can reduce plating margin and make drilling tolerance failures more likely.",
                    trigger_condition="Annular-ring width fell below the configured manufacturability threshold.",
                    threshold_label=f"Minimum annular ring {min_annular_ring:.2f}",
                    observed_label=f"Observed annular ring {annular_ring:.2f}",
                )
            )

        for component in getattr(pcb, "components", []):
            for pad in getattr(component, "pads", []):
                if _distance(via.x, via.y, pad.x, pad.y) <= via_in_pad_distance:
                    risks.append(
                        make_risk(
                            rule_id="manufacturability",
                            category="manufacturing",
                            severity="medium",
                            message=f"Via on net {via.net_name} is very close to pad {component.ref}:{pad.pad_name}",
                            recommendation="Review whether this is an intentional via-in-pad or near-pad escape and confirm fabrication/assembly strategy.",
                            components=[component.ref],
                            nets=[via.net_name],
                            metrics={
                                "distance": round(_distance(via.x, via.y, pad.x, pad.y), 3),
                                "threshold": via_in_pad_distance,
                            },
                            confidence=0.8,
                            short_title="Potential via-in-pad risk",
                            fix_priority="medium",
                            estimated_impact="moderate",
                            design_domain="manufacturing",
                            why_it_matters="Uncontrolled via-in-pad or near-pad escape can affect solderability and assembly yield.",
                            trigger_condition="Via-to-pad spacing fell below the configured near-pad manufacturability threshold.",
                            threshold_label=f"Minimum via-to-pad spacing {via_in_pad_distance:.2f}",
                            observed_label=f"Observed via-to-pad spacing {_distance(via.x, via.y, pad.x, pad.y):.2f}",
                        )
                    )
                    break

    return risks
