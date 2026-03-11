from engine.parser import start_engine, parse_pcb_file
from engine.analyzer import check_component_spacing

print("Starting Silicore...")

start_engine()

pcb_data = parse_pcb_file("sample_pcb.txt")

risks = check_component_spacing(pcb_data)

if risks:
    print("\nDesign Risks Found:")
    for r in risks:
        print(r)
else:
    print("\nNo spacing risks detected.")