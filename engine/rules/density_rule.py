from engine.risk import make_risk


def run_rule(pcb):
    region_size = 10
    max_components_per_region = 4
    risks = []
    regions = {}

    for component in pcb.components:
        region_x = int(component.x // region_size)
        region_y = int(component.y // region_size)
        region_key = (region_x, region_y)

        if region_key not in regions:
            regions[region_key] = []

        regions[region_key].append(component)

    for (region_x, region_y), components in regions.items():
        if len(components) > max_components_per_region:
            center_x = region_x * region_size
            center_y = region_y * region_size
            refs = [c.ref for c in components]

            risks.append(
                make_risk(
                    rule_id="density",
                    category="layout",
                    severity="medium",
                    message=f"High component density in region ({center_x},{center_y}) with {len(components)} components [{', '.join(refs)}]",
                    recommendation="Spread components more evenly to reduce routing congestion and assembly difficulty.",
                    components=refs,
                    region=(center_x, center_y),
                )
            )

    return risks