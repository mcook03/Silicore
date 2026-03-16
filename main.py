from collections import defaultdict
from engine.parser import start_engine, parse_pcb_file
from engine.rule_runner import run_analysis
from engine.visualizer import draw_board

print("Starting Silicore...")
start_engine()

pcb = parse_pcb_file("sample_pcb.txt")
risks, score = run_analysis(pcb)

grouped = defaultdict(list)
for risk in risks:
    grouped[risk["category"]].append(risk)

print("\nDesign Risks Found:")
if risks:
    for category, category_risks in grouped.items():
        print(f"\n== {category.upper()} ==")
        for risk in category_risks:
            print(f"[{risk['severity'].upper()}] {risk['message']}")
            if risk["recommendation"]:
                print(f"  Recommendation: {risk['recommendation']}")
else:
    print("No risks found.")

print(f"\nSilicore Risk Score: {score} / 10")

draw_board(pcb, risks)