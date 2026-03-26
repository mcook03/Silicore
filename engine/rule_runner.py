import importlib
import os


def calculate_score(risks):
    penalties = {
        "low": 0.5,
        "medium": 1.0,
        "high": 1.5,
        "critical": 2.0
    }

    score = 10.0
    total_penalty = 0.0

    for risk in risks:
        severity = str(risk.get("severity", "low")).lower()
        penalty = penalties.get(severity, 0.5)
        total_penalty += penalty

    score -= total_penalty

    if score < 0:
        score = 0.0

    return round(score, 2), round(total_penalty, 2)


def run_analysis(pcb, config):
    risks = []

    rules_dir = os.path.join(os.path.dirname(__file__), "rules")

    print("\n========== SILICORE RULE DEBUG ==========")
    print(f"Rules directory: {rules_dir}")
    print(f"PCB component count: {len(getattr(pcb, 'components', []))}")
    print(f"PCB net count: {len(getattr(pcb, 'nets', [])) if hasattr(pcb, 'nets') and pcb.nets else 0}")
    print(f"Config keys: {list(config.keys()) if isinstance(config, dict) else 'CONFIG NOT DICT'}")
    print("=========================================\n")

    for filename in os.listdir(rules_dir):
        if not filename.endswith(".py"):
            continue
        if filename == "__init__.py":
            continue

        module_name = f"engine.rules.{filename[:-3]}"
        print(f"Loading rule module: {module_name}")

        try:
            module = importlib.import_module(module_name)
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

    score, total_penalty = calculate_score(risks)

    print("\n============= FINAL DEBUG =============")
    print(f"Total risks found: {len(risks)}")
    print(f"Total penalty: {total_penalty}")
    print(f"Final score: {score} / 10")
    print("=======================================\n")

    return {
        "risks": risks,
        "score": score,
        "total_penalty": total_penalty
    }