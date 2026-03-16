import json


def export_analysis_to_json(pcb, risks, score, output_file="silicore_analysis.json"):
    data = {
        "summary": {
            "component_count": len(pcb.components),
            "net_count": len(pcb.nets),
            "risk_score": score,
            "total_risks": len(risks),
        },
        "risks": risks,
    }

    with open(output_file, "w") as file:
        json.dump(data, file, indent=4)

    return output_file