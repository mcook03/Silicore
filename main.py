from engine.parser import start_engine, parse_pcb_file
from engine.analyzer import run_analysis
from engine.visualizer import draw_board

print("Starting Silicore...")
start_engine()

pcb = parse_pcb_file("sample_pcb.txt")

risks, score = run_analysis(pcb)

print("\nDesign Risks Found:")

if risks:
    for risk in risks:
        print(risk)
else:
    print("No risks found.")

print(f"\nSilicore Risk Score: {score} / 10")

draw_board(pcb, risks)