def explain_risk(risk):
    explanation = {
        "root_cause": "",
        "impact": "",
        "confidence": risk.get("confidence", 0.8),
    }

    category = risk.get("category", "")

    if category == "power_integrity":
        explanation["root_cause"] = "Power delivery path impedance or placement issue"
        explanation["impact"] = "Voltage drop, instability, or noise"

    elif category == "signal_integrity":
        explanation["root_cause"] = "Signal path geometry or routing issue"
        explanation["impact"] = "Timing errors or signal degradation"

    elif category == "layout":
        explanation["root_cause"] = "Component placement constraint violation"
        explanation["impact"] = "Routing congestion or manufacturability issues"

    elif category == "manufacturing":
        explanation["root_cause"] = "Design rule below fabrication limits"
        explanation["impact"] = "Reduced yield or board failure risk"

    elif category == "emi_return_path":
        explanation["root_cause"] = "Missing or poor return path"
        explanation["impact"] = "Increased EMI and unstable signal reference"

    elif category == "thermal":
        explanation["root_cause"] = "Thermal concentration or poor heat spreading"
        explanation["impact"] = "Hotspots, reduced reliability, or thermal stress"

    else:
        explanation["root_cause"] = "General design issue"
        explanation["impact"] = "Unknown system impact"

    return explanation