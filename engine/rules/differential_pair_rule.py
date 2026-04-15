from engine.risk import make_risk


def _pair_base_name(net_name):
    upper = str(net_name).strip().upper()
    suffixes = ["_DP", "_DN", "_P", "_N", "+", "-"]
    for suffix in suffixes:
        if upper.endswith(suffix):
            return upper[: -len(suffix)], suffix
    return None, None


def run_rule(pcb, config):
    risks = []
    rule_config = config.get("rules", {}).get("differential_pair", {})

    mismatch_threshold = float(rule_config.get("length_mismatch_threshold", 5.0))
    via_mismatch_threshold = int(rule_config.get("via_mismatch_threshold", 1))

    pairs = {}
    for net_name in getattr(pcb, "nets", {}).keys():
        base_name, suffix = _pair_base_name(net_name)
        if not base_name:
            continue
        pairs.setdefault(base_name, {})[suffix] = str(net_name).strip().upper()

    for base_name, pair in pairs.items():
        positive = pair.get("_DP") or pair.get("_P") or pair.get("+")
        negative = pair.get("_DN") or pair.get("_N") or pair.get("-")
        if not positive or not negative:
            continue

        positive_length = pcb.total_trace_length_for_net(positive)
        negative_length = pcb.total_trace_length_for_net(negative)
        length_mismatch = abs(positive_length - negative_length)

        if length_mismatch > mismatch_threshold:
            risks.append(
                make_risk(
                    rule_id="differential_pair",
                    category="high_speed",
                    severity="high",
                    message=f"Differential pair {base_name} has a length mismatch of {length_mismatch:.2f} units",
                    recommendation="Length-match the positive and negative pair routes more closely to reduce skew.",
                    nets=[positive, negative],
                    metrics={
                        "positive_length": round(positive_length, 2),
                        "negative_length": round(negative_length, 2),
                        "length_mismatch": round(length_mismatch, 2),
                        "threshold": mismatch_threshold,
                    },
                    confidence=0.9,
                    short_title="Differential pair skew risk",
                    fix_priority="high",
                    estimated_impact="high",
                    design_domain="signal",
                    why_it_matters="Differential pair skew can collapse timing margin and degrade signal integrity on high-speed links.",
                    trigger_condition="Differential-pair route length mismatch exceeded the configured skew threshold.",
                    threshold_label=f"Maximum pair mismatch {mismatch_threshold:.2f} units",
                    observed_label=f"Observed pair mismatch {length_mismatch:.2f} units",
                )
            )

        positive_vias = pcb.via_count_for_net(positive)
        negative_vias = pcb.via_count_for_net(negative)
        via_mismatch = abs(positive_vias - negative_vias)

        if via_mismatch > via_mismatch_threshold:
            risks.append(
                make_risk(
                    rule_id="differential_pair",
                    category="high_speed",
                    severity="medium",
                    message=f"Differential pair {base_name} uses unbalanced via transitions ({positive_vias} vs {negative_vias})",
                    recommendation="Keep differential pair layer transitions balanced across both members of the pair.",
                    nets=[positive, negative],
                    metrics={
                        "positive_vias": positive_vias,
                        "negative_vias": negative_vias,
                        "via_mismatch": via_mismatch,
                        "threshold": via_mismatch_threshold,
                    },
                    confidence=0.84,
                    short_title="Differential via asymmetry",
                    fix_priority="medium",
                    estimated_impact="moderate",
                    design_domain="signal",
                    why_it_matters="Unbalanced transitions can disturb pair symmetry and worsen differential conversion or skew.",
                    trigger_condition="Differential-pair via mismatch exceeded the configured symmetry threshold.",
                    threshold_label=f"Maximum pair via mismatch {via_mismatch_threshold}",
                    observed_label=f"Observed pair via mismatch {via_mismatch}",
                )
            )

    return risks
