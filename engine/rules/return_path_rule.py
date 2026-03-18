from math import sqrt

from engine.risk import make_risk
from engine.net_utils import is_excluded_net, is_critical_signal_net


def distance(c1, c2):
    return sqrt((c1.x - c2.x) ** 2 + (c1.y - c2.y) ** 2)


def run_rule(pcb, config):
    risks = []
    rule_config = config["rules"]["signal_path"]

    threshold = rule_config["threshold"]
    excluded_net_keywords = rule_config["excluded_net_keywords"]
    critical_net_keywords = rule_config["critical_net_keywords"]

    for net_name, net in pcb.nets.items():
        if is_excluded_net(net_name, excluded_net_keywords):
            continue

        if not is_critical_signal_net(net_name, critical_net_keywords):
            continue

        valid_connections = [conn for conn in net.connections if conn[0]]
        if len(valid_connections) < 2:
            continue

        max_pair_distance = 0.0
        worst_pair = None

        for i in range(len(valid_connections)):
            for j in range(i + 1, len(valid_connections)):
                ref1, _ = valid_connections[i]
                ref2, _ = valid_connections[j]

                c1 = pcb.get_component(ref1)
                c2 = pcb.get_component(ref2)

                if c1 is None or c2 is None:
                    continue

                d = distance(c1, c2)

                if d > max_pair_distance:
                    max_pair_distance = d
                    worst_pair = (c1, c2)

        if worst_pair and max_pair_distance > threshold:
            c1, c2 = worst_pair
            risks.append(
                make_risk(
                    rule_id="signal_path",
                    category="signal_integrity",
                    severity="medium",
                    message=f"Critical net {net_name} has a long signal path between {c1.ref} and {c2.ref} ({max_pair_distance:.2f} units)",
                    recommendation="Reduce path length or improve routing on this critical signal to lower timing and noise risks.",
                    components=[c1.ref, c2.ref],
                    nets=[net_name],
                    metrics={
                        "distance": round(max_pair_distance, 2),
                        "threshold": threshold,
                    },
                    confidence=0.86,
                    short_title="Long critical signal path",
                    fix_priority="medium",
                    estimated_impact="moderate",
                    design_domain="signal",
                )
            )

    return risks