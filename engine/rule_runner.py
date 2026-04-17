import importlib
import os

RULE_CATEGORY_MAP = {
    "spacing_rule": "layout_manufacturing",
    "density_rule": "layout_manufacturing",
    "manufacturability_rule": "layout_manufacturing",
    "cam_geometry_rule": "layout_manufacturing",
    "cam_bundle_rule": "layout_manufacturing",
    "assembly_testability_rule": "layout_manufacturing",
    "power_connectivity_rule": "power",
    "power_distribution_rule": "power",
    "power_rail_rule": "power",
    "decoupling_rule": "power",
    "decoupling_strategy_rule": "power",
    "power_path_realism_rule": "power",
    "current_density_rule": "power",
    "signal_path_rule": "signal",
    "net_length_rule": "signal",
    "trace_quality_rule": "signal",
    "signal_integrity_advanced_rule": "signal",
    "differential_pair_rule": "signal",
    "component_analysis_rule": "signal",
    "clock_sensitive_placement_rule": "signal",
    "thermal_rule": "thermal",
    "thermal_management_rule": "thermal",
    "ground_reference_rule": "emi_reliability",
    "return_path_rule": "emi_reliability",
    "reliability_rule": "emi_reliability",
    "emi_emc_rule": "emi_reliability",
    "analog_isolation_rule": "emi_reliability",
    "stackup_return_path_rule": "emi_reliability",
    "safety_high_voltage_rule": "safety",
}


def _rule_is_enabled(filename, config):
    stem = filename[:-3]
    analysis = (config or {}).get("analysis", {}) or {}
    category_toggles = analysis.get("category_toggles", {}) or {}
    rule_toggles = analysis.get("rule_toggles", {}) or {}

    category_key = RULE_CATEGORY_MAP.get(stem)
    if category_key and category_toggles.get(category_key) is False:
        return False

    if rule_toggles.get(stem) is False:
        return False

    return True


def calculate_score(risks, config=None):
    score_config = (config or {}).get("score", {})

    penalties = score_config.get(
        "severity_penalties",
        {
            "low": 0.5,
            "medium": 1.0,
            "high": 1.5,
            "critical": 2.0,
        },
    )

    start_score = float(score_config.get("start_score", 10.0))
    min_score = float(score_config.get("min_score", 0.0))
    max_score = float(score_config.get("max_score", 10.0))

    total_penalty = 0.0

    for risk in risks:
        severity = str(risk.get("severity", "low")).lower()
        total_penalty += float(penalties.get(severity, 0.5))

    score = start_score - total_penalty
    score = max(min_score, min(max_score, round(score, 2)))

    return round(score, 2), round(total_penalty, 2)


def run_analysis(pcb, config):
    risks = []
    rules_dir = os.path.join(os.path.dirname(__file__), "rules")

    print("\n========== SILICORE RULE DEBUG ==========")
    print(f"Rules directory: {rules_dir}")
    print(f"PCB component count: {len(getattr(pcb, 'components', []))}")
    print(
        f"PCB net count: {len(getattr(pcb, 'nets', {})) if hasattr(pcb, 'nets') and pcb.nets else 0}"
    )
    print(
        f"Config keys: {list(config.keys()) if isinstance(config, dict) else 'CONFIG NOT DICT'}"
    )
    print("=========================================\n")

    for filename in sorted(os.listdir(rules_dir)):
        if not filename.endswith(".py"):
            continue
        if filename == "__init__.py":
            continue
        if not _rule_is_enabled(filename, config):
            print(f"Skipping disabled rule module: {filename}")
            continue

        module_name = f"engine.rules.{filename[:-3]}"
        print(f"Loading rule module: {module_name}")

        try:
            module = importlib.import_module(module_name)
            module = importlib.reload(module)
        except Exception as e:
            print(f"FAILED TO IMPORT {module_name}: {e}")
            continue

        if not hasattr(module, "run_rule"):
            print(f"SKIPPING {module_name}: no run_rule function found")
            continue

        try:
            rule_risks = module.run_rule(pcb, config)

            if rule_risks is None:
                print(f"{module_name} returned None")
                rule_risks = []

            if not isinstance(rule_risks, list):
                print(f"{module_name} returned non-list: {type(rule_risks)}")
                rule_risks = []

            print(f"{module_name} produced {len(rule_risks)} risk(s)")

            for risk in rule_risks:
                print(
                    f"  - [{risk.get('severity', 'unknown').upper()}] "
                    f"{risk.get('rule_id', 'no_rule_id')}: "
                    f"{risk.get('message', 'no message')}"
                )

            risks.extend(rule_risks)

        except Exception as e:
            print(f"ERROR RUNNING {module_name}: {e}")

    score, total_penalty = calculate_score(risks, config)

    print("\n============= FINAL DEBUG =============")
    print(f"Total risks found: {len(risks)}")
    print(f"Total penalty: {total_penalty}")
    print(f"Core rule score: {score} / 10")
    print("Final product score may differ after service-level scaling, soft-floor protection, and physics-informed adjustments.")
    print("=======================================\n")

    return {
        "risks": risks,
        "score": score,
        "total_penalty": total_penalty,
    }
