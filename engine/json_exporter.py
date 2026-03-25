import json


def export_analysis_to_json(analysis_result, output_path):
    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(analysis_result, file, indent=4)