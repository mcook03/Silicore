from engine.parser import start_engine, parse_pcb_file
from engine.rule_runner import run_analysis
from engine.visualizer import draw_board
from engine.report_generator import generate_report
from engine.json_exporter import export_analysis_to_json

print("Starting Silicore...")
start_engine()

pcb = parse_pcb_file("sample_pcb.txt")
risks, score = run_analysis(pcb)

report = generate_report(pcb, risks, score)
print()
print(report)
print()

with open("silicore_report.txt", "w") as file:
    file.write(report)

print("Report saved to silicore_report.txt")

json_file = export_analysis_to_json(pcb, risks, score)
print(f"JSON analysis saved to {json_file}")

draw_board(pcb, risks)