def check_component_density(pcb, region_size=10, max_components_per_region=4):
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
            refs = ", ".join(c.ref for c in components)

            risks.append(
                f"Risk: High component density in region ({center_x},{center_y}) "
                f"with {len(components)} components [{refs}]"
            )

    return risks