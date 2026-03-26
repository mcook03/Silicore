import math
from engine.risk import make_risk


EXCLUDED_NETS = {"GND", "GROUND", "VCC", "VIN", "VBAT", "3V3", "5V", "12V", "VDD"}


def find_component_by_ref(pcb, ref):
    for component in getattr(pcb, "components", []):
        if getattr(component, "ref", None) == ref:
            return component
    return None


def calculate_distance(component_a, component_b):
    dx = getattr(component_a, "x", 0) - getattr(component_b, "x", 0)
    dy = getattr(component_a, "y", 0) - getattr(component_b, "y", 0)
    return math.sqrt((dx ** 2) + (dy ** 2))


def run_rule(pcb, config):
    risks = []

    rule_config = config.get("rules", {}).get("net_length", {})
    signal_config = config.get("signal", {})

    max_trace_length = float(
        rule_config.get(
            "max_trace_length",
            signal_config.get("max_trace_length", 25.0),
        )
    )

    critical_nets = rule_config.get(
        "critical_nets",
        signal_config.get("critical_nets", ["CLK", "DATA", "CTRL"]),
    )

    normalized_critical_nets = {str(net).upper() for net in critical_nets}

    for net_name, net in getattr(pcb, "nets", {}).items():
        normalized_net_name = str(net_name).upper()

        if normalized_net_name in EXCLUDED_NETS:
            continue

        connections = getattr(net, "connections", [])

        if not connections or len(connections) < 2:
            continue

        refs = []
        for connection in connections:
            ref = connection[0]
            if ref and ref not in refs:
                refs.append(ref)

        if len(refs) < 2:
            continue

        for i in range(len(refs)):
            for j in range(i + 1, len(refs)):
                ref_a = refs[i]
                ref_b = refs[j]

                component_a = find_component_by_ref(pcb, ref_a)
                component_b = find_component_by_ref(pcb, ref_b)

                if not component_a or not component_b:
                    continue

                distance = calculate_distance(component_a, component_b)

                if distance > max_trace_length:
                    is_critical = normalized_net_name in normalized_critical_nets
                    severity = "high" if is_critical else "medium"

                    risks.append(
                        make_risk(
                            rule_id="net_length",
                            category="signal_integrity",
                            severity=severity,
                            message=f"Net {net_name} has a long path between {ref_a} and {ref_b} ({distance:.2f} units)",
                            recommendation="Reduce routing distance, improve placement, or treat the net as timing-sensitive if appropriate.",
                            components=[ref_a, ref_b],
                            nets=[net_name],
                            metrics={
                                "distance": round(distance, 2),
                                "threshold": max_trace_length,
                                "is_critical_net": is_critical,
                            },
                            confidence=0.84 if is_critical else 0.78,
                            short_title="Long net path",
                            fix_priority="medium",
                            estimated_impact="moderate",
                            design_domain="signal",
                        )
                    )

    return risks