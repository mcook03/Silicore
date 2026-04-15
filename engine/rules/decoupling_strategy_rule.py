from math import sqrt

from engine.risk import make_risk


def _distance(a, b):
    return sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)


def _text(component):
    return f"{getattr(component, 'ref', '')} {getattr(component, 'value', '')} {getattr(component, 'type', '')}".lower()


def _matches(component, keywords):
    text = _text(component)
    return any(str(keyword).lower() in text for keyword in keywords)


def _is_cap(component, keywords):
    return getattr(component, "ref", "").upper().startswith("C") or _matches(component, keywords)


def _component_nets(component):
    nets = []
    for pad in getattr(component, "pads", []) or []:
        net_name = getattr(pad, "net_name", None)
        if net_name and net_name not in nets:
            nets.append(net_name)
    return nets


def run_rule(pcb, config):
    risks = []
    rule_config = ((config or {}).get("rules") or {}).get("decoupling_strategy", {})
    power_config = (config or {}).get("power") or {}

    local_threshold = float(rule_config.get("local_distance_threshold", power_config.get("decoupling_distance_threshold", 4.0)))
    bulk_threshold = float(rule_config.get("bulk_distance_threshold", 12.0))
    local_cap_count = int(rule_config.get("min_local_caps", 1))
    target_keywords = rule_config.get(
        "target_keywords",
        ["mcu", "cpu", "fpga", "soc", "adc", "dac", "sensor", "driver", "ic", "controller", "regulator", "pmic"],
    )
    capacitor_keywords = rule_config.get("capacitor_keywords", ["cap", "capacitor"])
    bulk_keywords = rule_config.get("bulk_keywords", ["10u", "22u", "47u", "100u", "bulk", "electrolytic", "tantalum"])

    components = getattr(pcb, "components", []) or []
    capacitors = [component for component in components if _is_cap(component, capacitor_keywords)]

    for component in components:
        if not _matches(component, target_keywords):
            continue

        component_nets = set(_component_nets(component))
        if not component_nets:
            continue

        local_caps = []
        bulk_caps = []

        for other in capacitors:
            if other.ref == component.ref:
                continue
            other_nets = set(_component_nets(other))
            if not (component_nets & other_nets):
                continue
            distance = _distance(component, other)
            if distance <= local_threshold:
                local_caps.append((other, distance))
            if distance <= bulk_threshold and _matches(other, bulk_keywords):
                bulk_caps.append((other, distance))

        if len(local_caps) < local_cap_count:
            nearest = min([distance for _, distance in local_caps], default=None)
            risks.append(
                make_risk(
                    rule_id="decoupling_strategy",
                    category="power_integrity",
                    severity="high",
                    message=f"{component.ref} appears to lack enough local decoupling support",
                    recommendation="Add or reposition local bypass capacitors close to the device supply pins with short return paths.",
                    components=[component.ref] + [cap.ref for cap, _ in local_caps[:2]],
                    nets=list(component_nets)[:4],
                    metrics={
                        "local_caps_found": len(local_caps),
                        "min_local_caps": local_cap_count,
                        "nearest_local_cap_distance": round(nearest, 2) if nearest is not None else None,
                    },
                    confidence=0.87,
                    short_title="Weak local decoupling strategy",
                    fix_priority="high",
                    estimated_impact="high",
                    design_domain="power",
                    trigger_condition="Component power pins did not have enough nearby local decoupling capacitors within the configured local-support radius.",
                    threshold_label=f"Minimum local capacitors {local_cap_count} within {local_threshold:.2f} units",
                    observed_label=f"Observed {len(local_caps)} local capacitors",
                )
            )

        if not bulk_caps and _matches(component, ["reg", "ldo", "buck", "boost", "pmic", "driver"]):
            risks.append(
                make_risk(
                    rule_id="decoupling_strategy_bulk",
                    category="power_integrity",
                    severity="medium",
                    message=f"{component.ref} may be missing nearby bulk capacitance support",
                    recommendation="Place appropriate bulk capacitance near the converter or regulator input/output path to reduce transients and rail collapse risk.",
                    components=[component.ref],
                    nets=list(component_nets)[:4],
                    metrics={
                        "bulk_caps_found": len(bulk_caps),
                        "bulk_distance_threshold": bulk_threshold,
                    },
                    confidence=0.79,
                    short_title="Missing bulk support near regulator",
                    fix_priority="medium",
                    estimated_impact="moderate",
                    design_domain="power",
                    trigger_condition="No likely bulk capacitor was found inside the configured regulator-support radius.",
                    threshold_label=f"Bulk support radius {bulk_threshold:.2f} units",
                    observed_label="Observed bulk capacitors: none found",
                )
            )

    return risks
