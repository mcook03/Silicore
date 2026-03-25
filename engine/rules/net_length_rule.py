import math


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

    signal_config = config.get("signal", {})
    max_trace_length = signal_config.get("max_trace_length", 50)
    critical_nets = signal_config.get("critical_nets", ["CLK", "DATA", "CTRL"])
    normalized_critical_nets = [net.upper() for net in critical_nets]

    for net_name, connected_refs in getattr(pcb, "nets", {}).items():
        if not connected_refs or len(connected_refs) < 2:
            continue

        for i in range(len(connected_refs)):
            for j in range(i + 1, len(connected_refs)):
                ref_a = connected_refs[i]
                ref_b = connected_refs[j]

                component_a = find_component_by_ref(pcb, ref_a)
                component_b = find_component_by_ref(pcb, ref_b)

                if not component_a or not component_b:
                    continue

                distance = calculate_distance(component_a, component_b)

                if distance > max_trace_length:
                    severity = "high" if str(net_name).upper() in normalized_critical_nets else "medium"

                    risks.append({
                        "rule_id": "net_length",
                        "category": "signal_integrity",
                        "severity": severity,
                        "message": f"Net {net_name} has a long path between {ref_a} and {ref_b} ({distance:.2f} units)",
                        "recommendation": "Reduce routing distance, improve placement, or treat the net as timing-sensitive if appropriate",
                        "components": [ref_a, ref_b],
                        "nets": [net_name],
                        "metrics": {
                            "distance": round(distance, 2),
                            "threshold": max_trace_length,
                            "is_critical_net": str(net_name).upper() in normalized_critical_nets
                        }
                    })

    return risks