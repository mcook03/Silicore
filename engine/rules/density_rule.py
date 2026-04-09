from collections import defaultdict
from engine.risk import make_risk


def run_rule(pcb, config):
    risks = []
    rule_config = config.get("rules", {}).get("density", {})
    layout_config = config.get("layout", {})

    region_size = float(
        rule_config.get(
            "region_size",
            layout_config.get("density_region_size", 25.0),
        )
    )
    component_threshold = int(
        rule_config.get(
            "component_threshold",
            layout_config.get("density_threshold", 6),
        )
    )

    grid = defaultdict(list)

    for comp in getattr(pcb, "components", []):
        region_x = int(comp.x // region_size) * int(region_size)
        region_y = int(comp.y // region_size) * int(region_size)
        key = (region_x, region_y)
        grid[key].append(comp)

    for region, comps in grid.items():
        if len(comps) > component_threshold:
            refs = [c.ref for c in comps]

            risks.append(
                make_risk(
                    rule_id="density",
                    category="layout",
                    severity="medium",
                    message=f"High component density in region {region} with {len(comps)} components [{', '.join(refs)}]",
                    recommendation="Spread components more evenly to reduce routing congestion and assembly difficulty.",
                    components=refs,
                    region=region,
                    metrics={
                        "component_count": len(comps),
                        "threshold": component_threshold,
                        "region_size": region_size,
                    },
                    confidence=0.9,
                    short_title="High component density",
                    fix_priority="medium",
                    estimated_impact="moderate",
                    design_domain="layout",
                )
            )

    return risks