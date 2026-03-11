from engine.parser import start_engine, parse_pcb_file
from engine.analyzer import check_component_spacing
from engine.analyzer import check_decoupling_capacitors
from engine.visualizer import draw_board


print("Starting Silicore...")

start_engine()

pcb = parse_pcb_file("sample_pcb.txt")

risks = check_component_spacing(pcb)

if risks:
    print("\nDesign Risks Found:")
    for r in risks:
        print(r)
else:
    print("\nNo spacing risks detected.")

decap_risks = check_decoupling_capacitors(pcb)

for r in decap_risks:
    print(r)

draw_board(pcb)



